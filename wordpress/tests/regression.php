<?php
require __DIR__.'/bootstrap.php';

function check($condition,$message) { if(!$condition) { throw new RuntimeException($message); } }
function expect_error($status,$fn) {
    try { $fn(); } catch(TLGA_Exception $e) { check($e->getCode()===$status,'Expected HTTP '.$status.', got '.$e->getCode().': '.$e->getMessage()); return; }
    throw new RuntimeException('Expected failure with HTTP '.$status);
}
function fresh_reader() {
    global $wpdb;
    static $n=0; ++$n;
    $id=wp_insert_user(array('user_login'=>'fixture_reader_'.$n,'user_email'=>'reader'.$n.'@example.invalid','user_pass'=>'test-only-reader-password','role'=>'subscriber'));
    check(!is_wp_error($id),'Reader creation failed'); wp_set_current_user($id);
    $GLOBALS['stripe_fixture']=array('sessions'=>array(),'keys'=>array(),'creates'=>0,'posts'=>array(),'timeout_once'=>false);
    update_option('tlga_codes',array(),false);
    $wpdb->last_error='';
    return (int)$id;
}
function tlg_fixture_stripe($args,$path) {
    $f=&$GLOBALS['stripe_fixture']; $method=$args['method']??'GET';
    $body=array(); if(isset($args['body'])) { parse_str($args['body'],$body); }
    if($path==='checkout/sessions' && $method==='POST') {
        $key=$args['headers']['Idempotency-Key']??'';
        check($key!=='','Checkout creation must include an idempotency key');
        $f['posts'][]=array('key'=>$key,'body'=>$body);
        if(isset($f['keys'][$key])) {
            check($f['keys'][$key]['body']===$body,'A retry changed its original idempotent request body');
            $s=$f['keys'][$key]['response'];
        } else {
            ++$f['creates']; $id='cs_test_fixture'.$f['creates'];
            $s=array('id'=>$id,'url'=>'https://checkout.stripe.com/c/pay/'.$id,'mode'=>'payment','currency'=>'usd',
                'amount_total'=>(int)$body['line_items'][0]['price_data']['unit_amount'],'metadata'=>$body['metadata'],
                'status'=>'open','payment_status'=>'unpaid');
            $f['sessions'][$id]=$s; $f['keys'][$key]=array('body'=>$body,'response'=>$s);
        }
        if($f['timeout_once']) { $f['timeout_once']=false; return new WP_Error('http_request_failed','Simulated lost Stripe response after session creation'); }
    } elseif(preg_match('#^checkout/sessions/(cs_[A-Za-z0-9_]+)(/expire)?$#',$path,$m)) {
        check(isset($f['sessions'][$m[1]]),'Unknown fixture session'); $s=$f['sessions'][$m[1]];
        if(!empty($m[2])) {
            check($method==='POST','Expiration must be POST'); check($s['status']==='open','Only open sessions can expire');
            $s['status']='expired'; $f['sessions'][$m[1]]=$s;
        }
    } else { throw new RuntimeException('Unexpected Stripe API call: '.$method.' '.$path); }
    return array('headers'=>array(),'body'=>wp_json_encode($s),'response'=>array('code'=>200,'message'=>'OK'),'cookies'=>array());
}
function paid_session($id) {
    $GLOBALS['stripe_fixture']['sessions'][$id]['status']='complete';
    $GLOBALS['stripe_fixture']['sessions'][$id]['payment_status']='paid';
    return $GLOBALS['stripe_fixture']['sessions'][$id];
}
function payment_row($id) {
    global $wpdb;
    return $wpdb->get_row($wpdb->prepare('SELECT * FROM '.tlga_table('payments').' WHERE session_id=%s',$id),ARRAY_A);
}
function fail_query_once($pattern,$fn) {
    global $wpdb; $hits=0;
    $filter=function($sql) use($pattern,&$hits) {
        if($hits===0 && preg_match($pattern,$sql)) { ++$hits; return 'UPDATE tlg_nonexistent_failure_fixture SET missing_column=1'; }
        return $sql;
    };
    add_filter('query',$filter,999);
    try { $fn(); } finally { remove_filter('query',$filter,999); $wpdb->last_error=''; }
    check($hits===1,'The intended database failure was not injected');
}
$tests=array();

$tests['repeated clicks reuse one payable session']=function() {
    $uid=fresh_reader(); $first=tlga_checkout($uid,null,2500); $second=tlga_checkout($uid,null,2500);
    check($first===$second,'Repeated checkout returned a different session');
    check($GLOBALS['stripe_fixture']['creates']===1,'Duplicate Stripe session created');
};
$tests['simultaneous requests are serialized']=function() {
    $uid=fresh_reader(); $lease=tlga_mutex_acquire('checkout:'.$uid);
    try { expect_error(409,function() use($uid) { tlga_checkout($uid,null,2500); }); }
    finally { tlga_mutex_release($lease); }
    check($GLOBALS['stripe_fixture']['creates']===0,'A concurrent request reached Stripe');
};
$tests['stale lease can be recovered without stale-owner unlock']=function() {
    fresh_reader(); $name='tlga_mutex_'.hash('sha256','expired-fixture'); $old=wp_json_encode(array('token'=>'old','expires'=>time()-10));
    add_option($name,$old,'',false); $lease=tlga_mutex_acquire('expired-fixture');
    tlga_mutex_release(array('name'=>$name,'value'=>$old));
    check(get_option($name)===$lease['value'],'Stale owner deleted a newer lock');
    tlga_mutex_release($lease); check(get_option($name,null)===null,'Current owner could not release lock');
};
$tests['lost Stripe response recovers with the original request key']=function() {
    $uid=fresh_reader(); $GLOBALS['stripe_fixture']['timeout_once']=true;
    expect_error(502,function() use($uid) { tlga_checkout($uid,null,2500); });
    $retry=tlga_checkout($uid,null,2500);
    check($GLOBALS['stripe_fixture']['creates']===1,'Retry created a second payment session');
    check(payment_row($retry['session_id'])['status']==='pending','Recovered checkout was not persisted');
};
$tests['lost local transaction write does not create another Stripe session']=function() {
    $uid=fresh_reader();
    fail_query_once('/^INSERT INTO .*tlg_payments/i',function() use($uid) {
        expect_error(503,function() use($uid) { tlga_checkout($uid,null,2500); });
    });
    $retry=tlga_checkout($uid,null,2500);
    check($GLOBALS['stripe_fixture']['creates']===1,'Database recovery created a second Stripe session');
    check((int)payment_row($retry['session_id'])['user_id']===$uid,'Recovered transaction has the wrong owner');
};
$tests['a changed discount expires the old checkout first']=function() {
    $uid=fresh_reader(); $first=tlga_checkout($uid,null,2500);
    $code=array('id'=>'half','code'=>'HALF'); $second=tlga_checkout($uid,$code,1250);
    check($first['session_id']!==$second['session_id'],'Discount did not create a replacement');
    check($GLOBALS['stripe_fixture']['sessions'][$first['session_id']]['status']==='expired','Previous payable checkout was left open');
    check(payment_row($first['session_id'])['status']==='failed','Previous transaction was not closed');
    check((int)payment_row($second['session_id'])['amount']===1250,'New amount is incorrect');
};
$tests['asynchronous pending payment blocks another checkout']=function() {
    $uid=fresh_reader(); $first=tlga_checkout($uid,null,2500);
    $GLOBALS['stripe_fixture']['sessions'][$first['session_id']]['status']='complete';
    expect_error(409,function() use($uid) { tlga_checkout($uid,null,2500); });
    check($GLOBALS['stripe_fixture']['creates']===1,'Processing payment allowed another checkout');
};
$tests['expired checkout can be replaced']=function() {
    $uid=fresh_reader(); $first=tlga_checkout($uid,null,2500);
    $GLOBALS['stripe_fixture']['sessions'][$first['session_id']]['status']='expired';
    $second=tlga_checkout($uid,null,2500);
    check($first['session_id']!==$second['session_id'],'Expired checkout was reused');
};
$tests['free access closes an earlier payable checkout']=function() {
    $uid=fresh_reader(); $first=tlga_checkout($uid,null,2500);
    $result=tlga_checkout($uid,array('id'=>'gift','code'=>'GIFT'),0);
    check($result['granted'] && tlga_has_access($uid),'Free access was not saved');
    check($GLOBALS['stripe_fixture']['sessions'][$first['session_id']]['status']==='expired','Free access left a payable session open');
};
$tests['an access write failure prevents acknowledgement and can recover']=function() {
    $uid=fresh_reader(); $first=tlga_checkout($uid,null,2500); $session=paid_session($first['session_id']);
    fail_query_once('/^(INSERT INTO|UPDATE) .*usermeta.*tlga_access[\'", ]/is',function() use($session) {
        expect_error(503,function() use($session) { tlga_mark_paid($session); });
    });
    check(payment_row($first['session_id'])['status']==='pending','Failed access was recorded as fulfilled');
    check(!tlga_has_access($uid),'Failed database write unexpectedly granted access');
    check(tlga_mark_paid($session) && tlga_has_access($uid),'Retry did not restore access');
};
$tests['transaction status write failure returns 503 and recovers']=function() {
    $uid=fresh_reader(); $first=tlga_checkout($uid,null,2500); $session=paid_session($first['session_id']);
    fail_query_once('/^UPDATE .*tlg_payments.*SET status=\'paid\'/is',function() use($session) {
        expect_error(503,function() use($session) { tlga_mark_paid($session); });
    });
    check(payment_row($first['session_id'])['status']==='pending','Failed status write was silently accepted');
    check(tlga_mark_paid($session),'Retry did not acknowledge a persisted transaction');
    check(payment_row($first['session_id'])['status']==='paid','Retry did not persist paid status');
};
$tests['duplicate paid callbacks count a discount once']=function() {
    $uid=fresh_reader(); update_option('tlga_codes',array('half'=>array('uses'=>0)),false);
    $first=tlga_checkout($uid,array('id'=>'half','code'=>'HALF'),1250); $session=paid_session($first['session_id']);
    check(tlga_mark_paid($session) && tlga_mark_paid($session),'Repeated callback failed');
    check(get_option('tlga_codes')['half']['uses']===1,'Repeated payment counted the discount twice');
};
$tests['wrong owner amount currency and payment state cannot grant access']=function() {
    $uid=fresh_reader(); $first=tlga_checkout($uid,null,2500); $valid=paid_session($first['session_id']);
    foreach(array('owner','amount','currency','pending') as $case) {
        $s=$valid;
        if($case==='owner') { $s['metadata']['user_id']=(string)($uid+1); }
        if($case==='amount') { $s['amount_total']=1; }
        if($case==='currency') { $s['currency']='eur'; }
        if($case==='pending') { $s['payment_status']='unpaid'; }
        check(tlga_mark_paid($s)===false,'Invalid '.$case.' granted access');
        check(!tlga_has_access($uid),'Invalid callback changed access');
    }
};
$tests['webhook surfaces storage failure as HTTP 503']=function() {
    $uid=fresh_reader(); $first=tlga_checkout($uid,null,2500); $session=paid_session($first['session_id']);
    $raw=wp_json_encode(array('type'=>'checkout.session.completed','data'=>array('object'=>$session)));
    $request=new WP_REST_Request('POST','/tlg/v1/stripe/webhook'); $request->set_body($raw);
    $request->set_header('Content-Type','application/json'); $time=time();
    $request->set_header('Stripe-Signature','t='.$time.',v1='.hash_hmac('sha256',$time.'.'.$raw,TLG_STRIPE_WEBHOOK_SECRET));
    fail_query_once('/^UPDATE .*tlg_payments.*SET status=\'paid\'/is',function() use($request) {
        $response=tlga_dispatch($request);
        check(is_wp_error($response) && $response->get_error_data()['status']===503,'Webhook did not surface the retryable error');
    });
    $response=tlga_dispatch($request);
    check(!is_wp_error($response),'Webhook retry did not succeed');
};
$tests['invalid and stale signatures are rejected']=function() {
    fresh_reader();
    check(!tlga_stripe_signature('{}','t='.time().',v1=invalid',TLG_STRIPE_WEBHOOK_SECRET),'Invalid signature accepted');
    $time=time()-301; $sig=hash_hmac('sha256',$time.'.{}',TLG_STRIPE_WEBHOOK_SECRET);
    check(!tlga_stripe_signature('{}','t='.$time.',v1='.$sig,TLG_STRIPE_WEBHOOK_SECRET),'Expired signature accepted');
};
$tests['existing email account is never automatically linked']=function() {
    $uid=fresh_reader(); $u=get_userdata($uid); $hash=$u->user_pass;
    expect_error(409,function() use($u) { tlga_google_account(array('sub'=>'collision-subject','email'=>$u->user_email,'email_verified'=>true)); });
    check(get_user_meta($uid,'tlga_google_sub',true)==='','An existing account was linked by email');
    check(get_userdata($uid)->user_pass===$hash,'Existing password was changed');
};
$tests['new Google account binds a stable subject and survives an email change']=function() {
    fresh_reader(); $info=array('sub'=>'new-google-fixture','email'=>'google-new@example.invalid','email_verified'=>true,'name'=>'Fixture');
    $first=tlga_google_account($info);
    check($first['new'] && get_user_meta($first['id'],'tlga_google_sub',true)===$info['sub'],'New subject was not saved');
    $info['email']='google-renamed@example.invalid'; $again=tlga_google_account($info);
    check(!$again['new'] && $again['id']===$first['id'],'A provider email change broke subject-based sign-in');
};
$tests['unverified Google email cannot create or link accounts']=function() {
    fresh_reader();
    expect_error(403,function() { tlga_google_account(array('sub'=>'unverified-subject','email'=>'unverified@example.invalid','email_verified'=>false)); });
    check(!email_exists('unverified@example.invalid'),'Unverified email created an account');
};


$tests['pre-update pending checkout is recovered without another session']=function() {
    $uid=fresh_reader(); $first=tlga_checkout($uid,null,2500);
    delete_option('tlga_pending_checkout_'.$uid);
    $second=tlga_checkout($uid,null,2500);
    check($first===$second && $GLOBALS['stripe_fixture']['creates']===1,'A pre-update checkout was duplicated');
};
$tests['previously recorded paid transaction repairs missing access']=function() {
    $uid=fresh_reader(); $first=tlga_checkout($uid,null,2500); tlga_mark_paid(paid_session($first['session_id']));
    delete_user_meta($uid,'tlga_access');
    expect_error(409,function() use($uid) { tlga_checkout($uid,null,2500); });
    check(tlga_has_access($uid),'Recorded payment did not repair missing access');
    check($GLOBALS['stripe_fixture']['creates']===1,'Recorded payment allowed a second charge');
};

$passed=0;
foreach($tests as $name=>$fn) {
    try { $fn(); ++$passed; echo "PASS ".$name.PHP_EOL; }
    catch(Throwable $e) { fwrite(STDERR,"FAIL ".$name.": ".$e->getMessage().PHP_EOL); exit(1); }
}
echo $passed." regression checks passed against WordPress ".get_bloginfo('version')." / PHP ".PHP_VERSION.PHP_EOL;
