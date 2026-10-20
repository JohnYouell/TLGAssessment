<?php
if (!defined('ABSPATH')) { exit; }
function tlga_setting($key) {
    $defaults=tlga_defaults();
    $fallback=array('verses'=>array('verses'=>array(
      array('text'=>'Rather, train yourself to be godly.','ref'=>'1 Timothy 4:7','translation'=>'NIV'),
      array('text'=>'Run in such a way as to get the prize.','ref'=>'1 Corinthians 9:24','translation'=>'NIV'),
      array('text'=>'Let us run with perseverance the race marked out for us.','ref'=>'Hebrews 12:1','translation'=>'NIV'),
      array('text'=>'Those who hope in the Lord will renew their strength.','ref'=>'Isaiah 40:31','translation'=>'NIV')
    )), 'sharing'=>$defaults['DEFAULT_SHARING'],'endorsements'=>array('layout'=>'cards','items'=>array()),'videos'=>array('videos'=>array()));
    if(strpos($key,'page:')===0) { $fallback[$key]=$defaults['DEFAULT_PAGES'][substr($key,5)]??array(); }
    $data=get_option('tlga_'.$key,$fallback[$key]??array());
    if(strpos($key,'page:')===0 && !empty($data['photo_url']) && substr($data['photo_url'],0,1)==='/') { $relative=ltrim($data['photo_url'],'/'); $data['photo_url']=file_exists(get_theme_root().'/tlg-training/assets/'.$relative)?tlga_asset($relative):home_url($data['photo_url']); }
    if($key==='videos') {
      foreach(array('registration_thanks','initial_congrats','pastor_final','section_2','section_3','section_4','section_5','section_6') as $v) { if(!isset($data['videos'][$v])) { $data['videos'][$v]=array('title'=>'','url'=>''); } }
    }
    return $data;
}
function tlga_content_validate($key,$b) {
    if(strpos($key,'page:')===0) {
      $out=array('eyebrow'=>tlga_text($b,'eyebrow',40),'title'=>tlga_text($b,'title',80,true),'body'=>tlga_text($b,'body',8000,true),'photo_url'=>tlga_text($b,'photo_url',500));
      if(strpos($out['photo_url'],'..')!==false) { tlga_fail('Invalid image path.'); }
      if($out['photo_url'] && !preg_match('#^(https://[^\s]+|/[\w./-]+)$#',$out['photo_url'])) { tlga_fail('Use an HTTPS image URL or site path.'); } return $out;
    }
    if($key==='sharing') {
      $url=tlga_text($b,'book_url',500); if($url && !wp_http_validate_url($url)) { tlga_fail('Enter a valid book URL.'); }
      return array('book_url'=>$url,'share_subject'=>tlga_text($b,'share_subject',120,true),'share_message'=>tlga_text($b,'share_message',2000,true));
    }
    if($key==='verses') {
      $list=$b['verses']??array(); if(!is_array($list) || count($list)<1 || count($list)>30) { tlga_fail('Add between 1 and 30 verses.'); }
      $out=array(); foreach($list as $v) { if(!is_array($v)) { tlga_fail('Invalid verse.'); } $out[]=array('text'=>tlga_text($v,'text',300,true),'ref'=>tlga_text($v,'ref',60,true),'translation'=>tlga_text($v,'translation',20)); } return array('verses'=>$out);
    }
    if($key==='endorsements') {
      $layout=$b['layout']??''; if(!in_array($layout,array('cards','spotlight','list'),true) || !is_array($b['items']??null) || count($b['items'])>30) { tlga_fail('Invalid endorsements.'); }
      $items=array(); foreach($b['items'] as $i) {
        $books=$i['books']??array(); if(!is_array($books) || count($books)>10) { tlga_fail('Invalid books list.'); }
        $items[]=array('text'=>tlga_text($i,'text',1200,true),'name'=>tlga_text($i,'name',100,true),'position'=>tlga_text($i,'position',150),'books'=>array_values(array_filter(array_map(function($book) { if(!is_string($book) || mb_strlen($book)>200) { tlga_fail('Invalid book title.'); } return sanitize_text_field($book); },$books))));
      } return array('layout'=>$layout,'items'=>$items);
    }
    if($key==='videos') {
      $current=tlga_setting('videos'); $list=$b['videos']??null; if(!is_array($list)) { tlga_fail('Invalid videos.'); }
      foreach($list as $id=>$v) { if(!isset($current['videos'][$id])) { tlga_fail('Unknown video.'); } $url=tlga_text($v,'url',300); if($url && !preg_match('#^https://(www\.|player\.)?vimeo\.com/[^\s]+$#',$url)) { tlga_fail('Use a Vimeo HTTPS video URL.'); } $current['videos'][$id]=array('title'=>tlga_text($v,'title',120),'url'=>$url); }
      return $current;
    } tlga_fail('Not found.',404);
}
function tlga_code_key($code) { return strtolower(preg_replace('/\s+/','',$code)); }
function tlga_code_validate($b) {
    $name=tlga_text($b,'code',40,true); if(!preg_match('/^[a-z0-9_-]{2,40}$/',tlga_code_key($name))) { tlga_fail('Use letters, numbers, spaces, hyphens or underscores in an access code.'); }
    $percent=$b['percent_off']??0; $amount=$b['amount_off']??0;
    if(!is_numeric($percent) || floor($percent)!=$percent || $percent<0 || $percent>100 || !is_numeric($amount) || $amount<0 || $amount>25 || (($percent>0)===($amount>0))) { tlga_fail('Set either a percentage or dollar discount, up to $25.'); }
    return array('id'=>tlga_code_key($name),'code'=>$name,'percent_off'=>(int)$percent,'amount_off'=>round((float)$amount,2),'active'=>($b['active']??true)===true,'uses'=>0);
}
function tlga_find_code($b) {
    $code=tlga_text($b,'code',40); if(!$code) { return null; } $codes=get_option('tlga_codes',array()); $id=tlga_code_key($code);
    if(empty($codes[$id]) || !$codes[$id]['active']) { tlga_fail('That discount code isn’t valid.'); } return $codes[$id];
}
function tlga_price($code) { return max(0,2500-(int)round(2500*($code['percent_off']??0)/100)-(int)round(100*($code['amount_off']??0))); }
function tlga_grant($uid,$source) {
    update_user_meta($uid,'tlga_access_source',$source);
    update_user_meta($uid,'tlga_access_date',tlga_now());
    update_user_meta($uid,'tlga_access',1);
    wp_cache_delete($uid,'user_meta');
    if((int)get_user_meta($uid,'tlga_access',true)!==1) { tlga_fail('Payment confirmation could not save access. Please try again.',503); }
}
function tlga_code_use($key) { if(!$key) { return; } $codes=get_option('tlga_codes',array()); if(isset($codes[$key])) { $codes[$key]['uses']++; update_option('tlga_codes',$codes,false); } }
function tlga_stripe($path,$body=null,$idempotency_key='') {
    $key=tlga_config('TLG_STRIPE_SECRET_KEY'); if(!$key) { tlga_fail('Online checkout is not configured yet. Please contact support.',503); }
    $args=array('timeout'=>25,'headers'=>array('Authorization'=>'Bearer '.$key,'Stripe-Version'=>'2024-06-20'));
    if($body!==null) { $args['method']='POST'; $args['body']=http_build_query($body); $args['headers']['Content-Type']='application/x-www-form-urlencoded'; }
    if($body!==null && $idempotency_key!=='') { $args['headers']['Idempotency-Key']=$idempotency_key; }
    $r=wp_remote_request('https://api.stripe.com/v1/'.$path,$args); $data=is_wp_error($r)?null:json_decode(wp_remote_retrieve_body($r),true);
    if(is_wp_error($r) || wp_remote_retrieve_response_code($r)>=400 || !is_array($data)) { tlga_fail('Checkout is temporarily unavailable. Please try again shortly.',502); } return $data;
}
function tlga_mark_paid($session) {
    global $wpdb; $id=$session['id']??''; $table=tlga_table('payments'); $row=$wpdb->get_row($wpdb->prepare("SELECT * FROM $table WHERE session_id=%s",$id),ARRAY_A);
    if($wpdb->last_error) { tlga_fail('Payment confirmation could not read the transaction. Please try again.',503); }
    if(!$row || ($session['payment_status']??'')!=='paid' || ($session['currency']??'')!=='usd' || (int)($session['amount_total']??-1)!==(int)$row['amount'] || (int)($session['metadata']['user_id']??0)!==(int)$row['user_id']) { return false; }
    // Granting is idempotent; doing it before the acknowledgement also recovers a retry after interruption.
    tlga_grant((int)$row['user_id'],'stripe:'.$id);
    $changed=$wpdb->query($wpdb->prepare("UPDATE $table SET status='paid' WHERE session_id=%s AND status <> 'paid'",$id));
    if($changed===false) { tlga_fail('Payment confirmation could not save the transaction. Please try again.',503); }
    if($changed===0) {
        $status=$wpdb->get_var($wpdb->prepare("SELECT status FROM $table WHERE session_id=%s",$id));
        if($wpdb->last_error || $status!=='paid') { tlga_fail('Payment confirmation could not verify the saved transaction. Please try again.',503); }
    }
    if($changed===1) { tlga_code_use($row['code_id']); }
    return true;
}
function tlga_stripe_signature($raw,$header,$secret,$clock=null) {
    $parts=array(); foreach(explode(',',$header) as $part) { $kv=explode('=',$part,2); if(count($kv)===2) { $parts[$kv[0]][]=$kv[1]; } }
    $t=$parts['t'][0]??''; if(!ctype_digit($t) || abs(($clock??time())-(int)$t)>300 || !$secret) { return false; }
    $expected=hash_hmac('sha256',$t.'.'.$raw,$secret); foreach($parts['v1']??array() as $sig) { if(hash_equals($expected,$sig)) { return true; } } return false;
}

function tlga_checkout_save($uid,$intent) {
    $key='tlga_pending_checkout_'.$uid;
    if(get_option($key,null)===$intent) { return; }
    if(!update_option($key,$intent,false)) { tlga_fail('Checkout could not be saved. Please try again.',503); }
}
function tlga_checkout_record($session,$uid,$intent) {
    global $wpdb;
    $id=$session['id']??'';
    if(!is_string($id) || !preg_match('/^cs_[A-Za-z0-9_]+$/',$id) ||
       ($session['mode']??'')!=='payment' || ($session['currency']??'')!=='usd' ||
       (int)($session['amount_total']??-1)!==(int)$intent['amount'] ||
       (int)($session['metadata']['user_id']??0)!==(int)$uid) { tlga_fail('Checkout details could not be verified.',502); }
    $row=$wpdb->get_row($wpdb->prepare('SELECT * FROM '.tlga_table('payments').' WHERE session_id=%s',$id),ARRAY_A);
    if($wpdb->last_error) { tlga_fail('Checkout could not read the transaction. Please try again.',503); }
    if($row) {
        if((int)$row['user_id']!==$uid || (int)$row['amount']!==(int)$intent['amount'] || $row['code_id']!==$intent['code_id']) { tlga_fail('Checkout transaction details do not match.',503); }
        return $row;
    }
    $row=array('session_id'=>$id,'user_id'=>$uid,'amount'=>$intent['amount'],'code_id'=>$intent['code_id'],'status'=>'pending','created_at'=>tlga_now());
    if($wpdb->insert(tlga_table('payments'),$row)!==1) { tlga_fail('Checkout could not save the transaction. Please try again.',503); }
    return $row;
}
function tlga_checkout_result($session) {
    $url=$session['url']??'';
    if(!is_string($url) || !preg_match('#^https://checkout\\.stripe\\.com/#',$url)) { tlga_fail('Checkout could not be opened.',502); }
    return array('checkout_url'=>$url,'session_id'=>$session['id']);
}
function tlga_checkout($uid,$code,$total) {
    global $wpdb;
    $uid=(int)$uid; $code_id=$code['id']??''; $key='tlga_pending_checkout_'.$uid;
    $lock=tlga_mutex_acquire('checkout:'.$uid);
    try {
        if(tlga_has_access($uid)) { tlga_fail('You already have Full Access.',409); }
        $paid_id=$wpdb->get_var($wpdb->prepare('SELECT session_id FROM '.tlga_table('payments')." WHERE user_id=%d AND status='paid' LIMIT 1",$uid));
        if($wpdb->last_error) { tlga_fail('Previous payments could not be checked. Please try again.',503); }
        if($paid_id) {
            tlga_grant($uid,'stripe:'.$paid_id);
            tlga_fail('Full Access is already paid and has been restored. Reload your dashboard.',409);
        }
        $intent=get_option($key,null);
        if($intent===null) {
            // Recover a pre-update pending session instead of opening another.
            $legacy=$wpdb->get_results($wpdb->prepare('SELECT * FROM '.tlga_table('payments')." WHERE user_id=%d AND status='pending' ORDER BY created_at DESC LIMIT 2",$uid),ARRAY_A);
            if($wpdb->last_error) { tlga_fail('Previous checkouts could not be checked. Please try again.',503); }
            if(count($legacy)>1) { tlga_fail('Multiple older checkouts need reconciliation. Please contact support before paying again.',409); }
            if(count($legacy)===1) {
                $old=$legacy[0];
                $intent=array('body'=>array(),'amount'=>(int)$old['amount'],'code_id'=>$old['code_id'],'created_at'=>time(),
                    'idempotency_key'=>'tlg-legacy-'.$old['session_id'],'session_id'=>$old['session_id']);
                tlga_checkout_save($uid,$intent);
            }
        }
        if($intent!==null) {
            if(!is_array($intent) || !isset($intent['body'],$intent['amount'],$intent['code_id'],$intent['idempotency_key'],$intent['created_at'])) { tlga_fail('Your pending checkout needs a support review.',503); }
            if(empty($intent['session_id'])) {
                // Recover an uncertain creation using the original body and key.
                // Never reuse a potentially pruned Stripe key after 23 hours.
                if(time()-(int)$intent['created_at']>=23*HOUR_IN_SECONDS) { tlga_fail('Your pending checkout needs reconciliation. Please contact support before paying again.',409); }
                $created=tlga_stripe('checkout/sessions',$intent['body'],$intent['idempotency_key']);
                if(empty($created['id']) || !is_string($created['id'])) { tlga_fail('Checkout could not be recovered.',502); }
                $intent['session_id']=$created['id']; tlga_checkout_save($uid,$intent);
            }
            $session=tlga_stripe('checkout/sessions/'.rawurlencode($intent['session_id']));
            $row=tlga_checkout_record($session,$uid,$intent);
            if(($session['payment_status']??'')==='paid') {
                tlga_mark_paid($session); delete_option($key);
                tlga_fail('Your payment is confirmed and Full Access is unlocked. Reload your dashboard.',409);
            }
            $status=$session['status']??'';
            if($status==='complete' && $row['status']!=='failed') { tlga_fail('Your payment is still processing. Please wait before starting another checkout.',409); }
            if($status==='open' && (int)$intent['amount']===$total && $intent['code_id']===$code_id) { return tlga_checkout_result($session); }
            if($status==='open') {
                // A discount change must close the old payable session first.
                $expired=tlga_stripe('checkout/sessions/'.rawurlencode($session['id']).'/expire',array());
                if(($expired['status']??'')!=='expired') { tlga_fail('The previous checkout could not be closed. Please try again.',503); }
            } elseif($status!=='expired' && !($status==='complete' && $row['status']==='failed')) {
                tlga_fail('The previous checkout could not be verified. Please try again.',503);
            }
            $changed=$wpdb->query($wpdb->prepare('UPDATE '.tlga_table('payments')." SET status='failed' WHERE session_id=%s AND status <> 'paid'",$session['id']));
            if($changed===false || !delete_option($key)) { tlga_fail('The previous checkout could not be updated. Please try again.',503); }
        }
        // Free access codes also close any earlier payable checkout.
        if($total===0 && $code) { tlga_grant($uid,'code:'.$code['code']); tlga_code_use($code_id); return array('granted'=>true); }
        $u=get_userdata($uid);
        if(!$u) { tlga_fail('Please sign in again.',401); }
        $body=array('mode'=>'payment','line_items'=>array(array('price_data'=>array('currency'=>'usd','unit_amount'=>$total,'product_data'=>array('name'=>'The Lord’s Gym — Full Training Program')),'quantity'=>1)),
            'customer_email'=>$u->user_email,'success_url'=>home_url('/payment/success').'?session_id={CHECKOUT_SESSION_ID}','cancel_url'=>home_url('/payment/cancel'),
            'metadata'=>array('user_id'=>(string)$uid,'code'=>$code_id));
        $intent=array('body'=>$body,'amount'=>$total,'code_id'=>$code_id,'created_at'=>time(),'idempotency_key'=>'tlg-checkout-'.$uid.'-'.wp_generate_uuid4());
        tlga_checkout_save($uid,$intent);
        $session=tlga_stripe('checkout/sessions',$body,$intent['idempotency_key']);
        tlga_checkout_record($session,$uid,$intent);
        $intent['session_id']=$session['id']; tlga_checkout_save($uid,$intent);
        return tlga_checkout_result($session);
    } finally { tlga_mutex_release($lock); }
}

function tlga_content_payments($path,$r,$b) {
    global $wpdb;
    if($path==='/stripe/webhook') {
      $raw=$r->get_body(); if(!tlga_stripe_signature($raw,$r->get_header('stripe-signature'),tlga_config('TLG_STRIPE_WEBHOOK_SECRET'))) { tlga_fail('Invalid signature.',400); }
      $event=json_decode($raw,true); $type=$event['type']??''; $obj=$event['data']['object']??array();
      if(in_array($type,array('checkout.session.completed','checkout.session.async_payment_succeeded'),true)) { tlga_mark_paid($obj); }
      elseif(in_array($type,array('checkout.session.expired','checkout.session.async_payment_failed'),true)) { $wpdb->query($wpdb->prepare('UPDATE '.tlga_table('payments')." SET status='failed' WHERE session_id=%s AND status <> 'paid'",$obj['id']??'')); }
      return array('status'=>'ok');
    }
    if(strpos($path,'/payments/status/')===0) {
      $sid=$r['session_id']; $row=$wpdb->get_row($wpdb->prepare('SELECT * FROM '.tlga_table('payments').' WHERE session_id=%s AND user_id=%d',$sid,get_current_user_id()),ARRAY_A);
      if($wpdb->last_error) { tlga_fail('The transaction could not be read. Please try again.',503); }
      if(!$row) { tlga_fail('Transaction not found.',404); }
      if($row['status']==='paid' && !tlga_has_access()) { tlga_grant(get_current_user_id(),'stripe:'.$sid); }
      if($row['status']!=='paid') { $session=tlga_stripe('checkout/sessions/'.rawurlencode($sid)); if(tlga_mark_paid($session)) { $row['status']='paid'; } }
      return array('session_id'=>$sid,'status'=>$row['status']==='paid'?'completed':$row['status'],'payment_status'=>$row['status']);
    }
    if(strpos($path,'/payments/')===0) {
      tlga_rate('checkout:'.get_current_user_id(),20,15*MINUTE_IN_SECONDS); $code=tlga_find_code($b); $total=tlga_price($code);
      if($r['pay_action']==='quote') { return array('price'=>25,'percent_off'=>$code['percent_off']??0,'amount_off'=>$code['amount_off']??0,'total'=>$total/100); }
      return tlga_checkout(get_current_user_id(),$code,$total);
    }
    if(strpos($path,'/admin/codes')===0) {
      $codes=get_option('tlga_codes',array()); $key=$r['code_id']; $m=$r->get_method();
      if($m==='GET') { return array('codes'=>array_values($codes)); }
      if($m==='DELETE') { if(!isset($codes[$key])) { tlga_fail('Code not found.',404); } unset($codes[$key]); update_option('tlga_codes',$codes,false); return array('ok'=>true); }
      $v=tlga_code_validate($b);
      if($m==='POST') { $key=$v['id']; if(isset($codes[$key])) { tlga_fail('A code with that name already exists.'); } }
      else { if(!isset($codes[$key])) { tlga_fail('Code not found.',404); } $v['id']=$key; $v['code']=$codes[$key]['code']; $v['uses']=$codes[$key]['uses']; }
      $codes[$key]=$v; update_option('tlga_codes',$codes,false); return $v;
    }
    if($path==='/admin/invites') {
      $counts=$wpdb->get_results('SELECT user_id,source,COUNT(*) AS n FROM '.tlga_table('shares').' GROUP BY user_id,source',ARRAY_A); $stats=array();
      foreach($counts as $row) { $id=(int)$row['user_id']; $stats[$id]=$stats[$id]??array('spread'=>0,'train'=>0,'joined'=>0); $stats[$id][$row['source']]=(int)$row['n']; }
      $refs=get_users(array('meta_key'=>'tlga_referred_by','fields'=>'ID')); foreach($refs as $id) { $ref=(int)get_user_meta($id,'tlga_referred_by',true); $stats[$ref]=$stats[$ref]??array('spread'=>0,'train'=>0,'joined'=>0); $stats[$ref]['joined']++; }
      $rows=array(); foreach($stats as $id=>$stat) { $u=get_userdata($id); if($u) { $rows[]=array_merge($stat,array('name'=>$u->display_name,'email'=>$u->user_email,'shares'=>$stat['spread']+$stat['train'])); } }
      usort($rows,function($a,$b){ return ($b['joined']<=>$a['joined']) ?: ($b['shares']<=>$a['shares']); }); return array('rows'=>$rows);
    }
    $admin=strpos($path,'/admin/')===0; $key=$admin?substr($path,7):substr($path,1);
    if(strpos($key,'pages/')===0) { $key='page:'.$r['slug']; }
    if($admin) { $out=tlga_content_validate($key,$b); update_option('tlga_'.$key,$out,false); return tlga_setting($key); }
    $out=tlga_setting($key);
    if($key==='videos') { $out['has_access']=tlga_has_access(); if(!$out['has_access']) { foreach(array('pastor_final','section_2','section_3','section_4','section_5','section_6') as $k) { $out['videos'][$k]['url']=''; } } }
    return $out;
}