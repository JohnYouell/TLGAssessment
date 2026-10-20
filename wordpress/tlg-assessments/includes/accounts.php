<?php
if (!defined('ABSPATH')) { exit; }
function tlga_session($uid) {
    wp_set_current_user($uid);
    $capture=function($cookie) { $_COOKIE[LOGGED_IN_COOKIE]=$cookie; };
    add_action('set_logged_in_cookie',$capture); wp_set_auth_cookie($uid,true,is_ssl()); remove_action('set_logged_in_cookie',$capture);
    tlga_touch($uid); return tlga_public_user($uid);
}
function tlga_validate_password($value) {
    if(!is_string($value) || strlen($value)<12 || strlen($value)>128) { tlga_fail('Use a password between 12 and 128 characters.'); }
    return $value;
}
function tlga_new_user($name,$email,$password,$opt=false,$ref='') {
    if(!is_email($email) || !trim($name)) { tlga_fail('Enter your name and a valid email.'); }
    if(email_exists($email)) { tlga_fail('An account with this email already exists.'); }
    $id=wp_insert_user(array('user_login'=>'tlg_'.strtolower(wp_generate_password(18,false,false)),'user_email'=>$email,'user_pass'=>$password,'display_name'=>$name,'role'=>'subscriber'));
    if(is_wp_error($id)) { tlga_fail('Your account could not be created. Please try again.'); }
    update_user_meta($id,'tlga_member',1); update_user_meta($id,'tlga_marketing',$opt?1:0); update_user_meta($id,'tlga_reminders',1);
    $ref=ctype_digit((string)$ref)?(int)$ref:0; if($ref && get_userdata($ref) && $ref!==$id) { update_user_meta($id,'tlga_referred_by',$ref); }
    tlga_touch($id); tlga_queue_email('welcome',$id); if($opt) { wp_schedule_single_event(time()+5,'tlga_marketing_sync',array($id)); }
    return $id;
}
function tlga_accounts($path,$r,$b) {
    $uid=get_current_user_id(); $u=wp_get_current_user();
    if($path==='/auth/me') { return tlga_public_user(); }
    if($path==='/auth/register') {
      tlga_rate('signup:'.tlga_ip(),6,HOUR_IN_SECONDS); $name=tlga_text($b,'name',100,true); $email=strtolower(tlga_text($b,'email',254,true)); $password=tlga_validate_password($b['password']??null);
      $id=tlga_new_user($name,$email,$password,($b['marketing_opt_in']??false)===true,$b['referred_by']??'');
      return tlga_session($id);
    }
    if($path==='/auth/login') {
      $email=strtolower(tlga_text($b,'email',254,true)); tlga_rate('login:'.$email.':'.tlga_ip(),10,15*MINUTE_IN_SECONDS);
      $password=$b['password']??''; if(!is_string($password) || strlen($password)>128) { tlga_fail('Invalid email or password.',401); }
      $user=wp_authenticate($email,$password); if(is_wp_error($user)) { tlga_fail('Invalid email or password.',401); }
      delete_transient('tlgr_'.hash('sha256','login:'.$email.':'.tlga_ip())); $out=tlga_session($user->ID); do_action('wp_login',$user->user_login,$user); return $out;
    }
    if($path==='/auth/logout') { wp_logout(); unset($_COOKIE[LOGGED_IN_COOKIE]); return array('ok'=>true); }
    if($path==='/auth/refresh') { return array('ok'=>true); }
    if($path==='/auth/forgot-password') {
      $email=strtolower(tlga_text($b,'email',254,true)); tlga_rate('reset-ip:'.tlga_ip(),15,HOUR_IN_SECONDS);
      $key='tlgr_'.hash('sha256','reset-email:'.$email); $count=(int)get_transient($key); $user=get_user_by('email',$email);
      if($count<3 && $user) {
        set_transient($key,$count+1,HOUR_IN_SECONDS); $reset=get_password_reset_key($user);
        if(!is_wp_error($reset)) { $token=rtrim(strtr(base64_encode($user->user_login.':'.$reset),'+/','-_'),'='); $url=add_query_arg('token',$token,home_url('/reset-password')); tlga_send_mail($user->user_email,'Reset your training password',tlga_email_html($user->display_name,'Reset your password','Use the button below to choose a new password. This link expires in one hour.','Reset Password',$url)); }
      } return array('ok'=>true);
    }
    if($path==='/auth/reset-password') {
      tlga_rate('reset-use:'.tlga_ip(),10,15*MINUTE_IN_SECONDS); $token=tlga_text($b,'token',500,true); $decoded=base64_decode(strtr($token,'-_','+/'),true); $parts=$decoded?explode(':',$decoded,2):array();
      if(count($parts)!==2) { tlga_fail('This reset link is invalid or has expired.'); }
      add_filter('password_reset_expiration','tlga_reset_expiry'); $user=check_password_reset_key($parts[1],$parts[0]); remove_filter('password_reset_expiration','tlga_reset_expiry');
      if(is_wp_error($user)) { tlga_fail('This reset link is invalid or has expired. Please request a new one.'); }
      $password=tlga_validate_password($b['password']??null); reset_password($user,$password); WP_Session_Tokens::get_instance($user->ID)->destroy_all(); delete_user_meta($user->ID,'tlga_google_only'); return tlga_session($user->ID);
    }
    if($path==='/account') {
      $name=tlga_text($b,'name',100,true); foreach(array('marketing_opt_in','reminders_opt_in') as $key) { if(!isset($b[$key]) || !is_bool($b[$key])) { tlga_fail('Please check your email preferences.'); } }
      wp_update_user(array('ID'=>$uid,'display_name'=>$name)); update_user_meta($uid,'tlga_marketing',$b['marketing_opt_in']?1:0); update_user_meta($uid,'tlga_reminders',$b['reminders_opt_in']?1:0); wp_schedule_single_event(time()+5,'tlga_marketing_sync',array($uid)); return tlga_public_user($uid);
    }
    if($path==='/auth/change-password' || $path==='/account/password') {
      tlga_rate('password:'.$uid,8,15*MINUTE_IN_SECONDS); $old=$b['current_password']??'';
      if(!get_user_meta($uid,'tlga_google_only',true) && (!is_string($old) || !wp_check_password($old,$u->user_pass,$uid))) { tlga_fail('Current password is incorrect.'); }
      $new=tlga_validate_password($b['new_password']??null); wp_set_password($new,$uid); WP_Session_Tokens::get_instance($uid)->destroy_all(); delete_user_meta($uid,'tlga_google_only'); return tlga_session($uid);
    }
    global $wpdb;
    if($path==='/sharing/event' || $path==='/share-events') {
      tlga_rate('share:'.$uid,20,HOUR_IN_SECONDS); $source=$b['source']??''; $channel=$b['channel']??'';
      if(!in_array($source,array('spread','train'),true) || !in_array($channel,array('email','sms','copy'),true)) { tlga_fail('Invalid sharing event.'); }
      $wpdb->insert(tlga_table('shares'),array('user_id'=>$uid,'source'=>$source,'channel'=>$channel,'created_at'=>tlga_now())); return array('ok'=>true);
    }
    if($path==='/account/invites') {
      $shares=(int)$wpdb->get_var($wpdb->prepare('SELECT COUNT(*) FROM '.tlga_table('shares').' WHERE user_id=%d',$uid));
      $members=get_users(array('meta_key'=>'tlga_referred_by','meta_value'=>$uid,'fields'=>'ID')); return array('shares'=>$shares,'joined'=>count($members));
    }
    tlga_fail('Not found.',404);
}
function tlga_reset_expiry() { return HOUR_IN_SECONDS; }

function tlga_google_account($info,$ref=0) {
    $subject=$info['sub']??'';
    if(($info['email_verified']??false)!==true || !is_string($subject) || $subject==='' || strlen($subject)>255 || !is_email($info['email']??'')) { tlga_fail('Google account details could not be verified.',403); }
    $lock=tlga_mutex_acquire('google:'.$subject);
    try {
        $matches=get_users(array('meta_key'=>'tlga_google_sub','meta_value'=>$subject,'fields'=>'ID','number'=>2));
        if(count($matches)>1) { tlga_fail('This Google account needs a support review before sign-in.',409); }
        if(count($matches)===1) {
            $uid=(int)$matches[0];
            if(!get_userdata($uid) || !hash_equals((string)get_user_meta($uid,'tlga_google_sub',true),$subject)) { tlga_fail('Google account binding could not be verified.',403); }
            return array('id'=>$uid,'new'=>false);
        }
        $email=strtolower($info['email']);
        if(email_exists($email)) {
            tlga_fail('An account already uses this email. Sign in with your password, or use Forgot Password to verify ownership. Automatic Google linking is disabled.',409);
        }
        $uid=tlga_new_user(sanitize_text_field($info['name']??$email),$email,wp_generate_password(40,true,true),false,$ref);
        update_user_meta($uid,'tlga_google_only',1);
        add_user_meta($uid,'tlga_google_sub',$subject,true);
        wp_cache_delete($uid,'user_meta');
        if(!hash_equals((string)get_user_meta($uid,'tlga_google_sub',true),$subject)) { tlga_fail('Google sign-in could not be saved. Use Forgot Password to recover this account.',503); }
        return array('id'=>$uid,'new'=>true);
    } finally { tlga_mutex_release($lock); }
}

function tlga_oauth() {
    if(get_query_var('tlg_route')!=='oauth/google') { return; }
    $client=tlga_config('TLG_GOOGLE_CLIENT_ID'); $secret=tlga_config('TLG_GOOGLE_CLIENT_SECRET');
    if(!$client || !$secret) { wp_die('Google sign-in has not been configured.', 'Google sign-in',array('response'=>503)); }
    $redirect=home_url('/oauth/google'); nocache_headers();
    if(empty($_GET['code'])) {
      if(isset($_GET['error'])) { wp_safe_redirect(home_url('/login')); exit; }
      $state=bin2hex(random_bytes(24)); $verifier=bin2hex(random_bytes(32));
      set_transient('tlga_oauth_'.hash('sha256',$state),array('verifier'=>$verifier,'ref'=>absint($_GET['ref']??0)),10*MINUTE_IN_SECONDS);
      setcookie('tlga_oauth',$state,array('expires'=>time()+600,'path'=>'/','secure'=>is_ssl(),'httponly'=>true,'samesite'=>'Lax'));
      $url=add_query_arg(array('client_id'=>$client,'redirect_uri'=>$redirect,'response_type'=>'code','scope'=>'openid email profile','state'=>$state,'code_challenge'=>rtrim(strtr(base64_encode(hash('sha256',$verifier,true)),'+/','-_'),'='),'code_challenge_method'=>'S256'),'https://accounts.google.com/o/oauth2/v2/auth');
      wp_redirect($url); exit;
    }
    $state=sanitize_text_field(wp_unslash($_GET['state']??'')); $cookie=$_COOKIE['tlga_oauth']??''; $saved=get_transient('tlga_oauth_'.hash('sha256',$state));
    if(!$saved || !$state || !hash_equals($cookie,$state)) { wp_die('Google sign-in expired. Please try again.','Google sign-in',array('response'=>403)); }
    delete_transient('tlga_oauth_'.hash('sha256',$state)); setcookie('tlga_oauth','',array('expires'=>time()-3600,'path'=>'/','secure'=>is_ssl(),'httponly'=>true,'samesite'=>'Lax'));
    $token=wp_remote_post('https://oauth2.googleapis.com/token',array('timeout'=>20,'body'=>array('code'=>sanitize_text_field(wp_unslash($_GET['code'])),'client_id'=>$client,'client_secret'=>$secret,'redirect_uri'=>$redirect,'grant_type'=>'authorization_code','code_verifier'=>$saved['verifier'])));
    $data=is_wp_error($token)?array():json_decode(wp_remote_retrieve_body($token),true);
    if(empty($data['access_token'])) { wp_die('Google sign-in could not be verified. Please try again.'); }
    $info=wp_remote_get('https://openidconnect.googleapis.com/v1/userinfo',array('timeout'=>20,'headers'=>array('Authorization'=>'Bearer '.$data['access_token'])));
    $info=is_wp_error($info)?array():json_decode(wp_remote_retrieve_body($info),true);
    if(empty($info['email_verified']) || empty($info['sub']) || !is_email($info['email']??'')) { wp_die('Google did not verify an email for this account.'); }
    try { $account=tlga_google_account($info,$saved['ref']); }
    catch(TLGA_Exception $e) { wp_die(esc_html($e->getMessage()),'Google sign-in',array('response'=>$e->getCode()?:400)); }
    tlga_session($account['id']); wp_safe_redirect(home_url($account['new']?'/welcome':'/dashboard')); exit;
}