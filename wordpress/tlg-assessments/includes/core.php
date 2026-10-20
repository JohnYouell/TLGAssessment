<?php
if (!defined('ABSPATH')) { exit; }
function tlga_data() { static $d; if (!$d) { $d = json_decode(file_get_contents(TLGA_DIR.'data/assessments.json'), true); } return $d; }
function tlga_defaults() { static $d; if (!$d) { $d = json_decode(file_get_contents(TLGA_DIR.'data/defaults.json'), true); } return $d; }
function tlga_table($name) { global $wpdb; return $wpdb->prefix.'tlg_'.$name; }
function tlga_now() { return gmdate('Y-m-d\TH:i:s\Z'); }
function tlga_asset($path) { return get_theme_root_uri().'/tlg-training/assets/'.ltrim($path, '/'); }
function tlga_config($name, $fallback = '') { return defined($name) ? constant($name) : $fallback; }
function tlga_fail($message, $status = 400) { throw new TLGA_Exception($message, $status); }
class TLGA_Exception extends RuntimeException {}
function tlga_activate() {
    global $wpdb; require_once ABSPATH.'wp-admin/includes/upgrade.php'; $c = $wpdb->get_charset_collate();
    dbDelta('CREATE TABLE '.tlga_table('progress')." (
      user_id bigint(20) unsigned NOT NULL,
      assessment_id smallint(5) unsigned NOT NULL,
      status varchar(20) NOT NULL DEFAULT 'in_progress',
      data longtext NOT NULL,
      updated_at varchar(32) NOT NULL,
      PRIMARY KEY  (user_id,assessment_id)
    ) $c;");
    dbDelta('CREATE TABLE '.tlga_table('payments')." (
      session_id varchar(191) NOT NULL,
      user_id bigint(20) unsigned NOT NULL,
      amount int NOT NULL,
      code_id varchar(80) NOT NULL DEFAULT '',
      status varchar(20) NOT NULL DEFAULT 'pending',
      created_at varchar(32) NOT NULL,
      PRIMARY KEY  (session_id),
      KEY user_id (user_id)
    ) $c;");
    dbDelta('CREATE TABLE '.tlga_table('shares')." (
      id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
      user_id bigint(20) unsigned NOT NULL,
      source varchar(10) NOT NULL,
      channel varchar(10) NOT NULL,
      created_at varchar(32) NOT NULL,
      PRIMARY KEY  (id),
      KEY user_id (user_id)
    ) $c;");
    add_option('tlga_codes', array(), '', false);
    if (!wp_next_scheduled('tlga_hourly')) { wp_schedule_event(time()+300, 'hourly', 'tlga_hourly'); }
    tlga_rewrites(); flush_rewrite_rules(); update_option('tlga_version', TLGA_VERSION, false);
}
function tlga_rewrites() {
    add_rewrite_rule('^((?:login|register|forgot-password|reset-password|welcome|dashboard|account|master-results|about|contact|book|spread-the-word|videos|oauth/google|congrats/initial|payment/(?:success|cancel)|assessment/[1-7](?:/result)?|admin/(?:verses|sharing|endorsements|codes|videos|invites|pages/(?:about|contact))))/?$', 'index.php?tlg_route=$matches[1]', 'top');
}
function tlga_public_user($id = 0) {
    $u = $id ? get_userdata($id) : wp_get_current_user();
    return array('id'=>(string)$u->ID, 'name'=>$u->display_name, 'email'=>$u->user_email,
      'marketing_opt_in'=>(bool)get_user_meta($u->ID,'tlga_marketing',true),
      'reminders_opt_in'=>!metadata_exists('user',$u->ID,'tlga_reminders') || (bool)get_user_meta($u->ID,'tlga_reminders',true),
      'has_password'=>!get_user_meta($u->ID,'tlga_google_only',true),
      'is_admin'=>user_can($u,'manage_options'), 'has_access'=>tlga_has_access($u->ID));
}
function tlga_has_access($uid = 0) { $uid = $uid ?: get_current_user_id(); return user_can($uid, 'manage_options') || (bool)get_user_meta($uid,'tlga_access',true); }
function tlga_touch($uid = 0) { $uid = $uid ?: get_current_user_id(); update_user_meta($uid,'tlga_activity',time()); delete_user_meta($uid,'tlga_nudge_sent'); }
function tlga_rate($scope, $limit, $seconds) {
    $key = 'tlgr_'.hash('sha256',$scope); $n = (int)get_transient($key);
    if ($n >= $limit) { tlga_fail('Too many attempts. Please try again later.',429); }
    set_transient($key,$n+1,$seconds);
}

function tlga_mutex_acquire($scope) {
    global $wpdb;
    $name='tlga_mutex_'.hash('sha256',$scope);
    $value=wp_json_encode(array('token'=>wp_generate_uuid4(),'expires'=>time()+300));
    if(add_option($name,$value,'',false)) { return array('name'=>$name,'value'=>$value); }
    $previous=get_option($name,'');
    $lease=is_string($previous)?json_decode($previous,true):null;
    if(!is_array($lease) || empty($lease['expires'])) { tlga_fail('The request lock could not be saved. Please try again.',503); }
    if((int)$lease['expires']>=time()) { tlga_fail('Another request is still being processed. Please wait and try again.',409); }
    $changed=$wpdb->query($wpdb->prepare("UPDATE {$wpdb->options} SET option_value=%s WHERE option_name=%s AND option_value=%s",$value,$name,$previous));
    wp_cache_delete($name,'options'); wp_cache_delete('notoptions','options');
    if($changed===false) { tlga_fail('The request lock could not be saved. Please try again.',503); }
    if($changed!==1) { tlga_fail('Another request is still being processed. Please wait and try again.',409); }
    return array('name'=>$name,'value'=>$value);
}
function tlga_mutex_release($lock) {
    global $wpdb;
    $changed=$wpdb->query($wpdb->prepare("DELETE FROM {$wpdb->options} WHERE option_name=%s AND option_value=%s",$lock['name'],$lock['value']));
    wp_cache_delete($lock['name'],'options'); wp_cache_delete('notoptions','options');
    if($changed===false) { error_log('The Lord\'s Gym: request lock release failed; the lease will expire.'); }
}

function tlga_ip() { return $_SERVER['REMOTE_ADDR'] ?? 'unknown'; }
function tlga_body($r) { $b = $r->get_json_params(); return is_array($b) ? $b : array(); }
function tlga_text($b, $key, $max, $required = false) {
    if (isset($b[$key]) && !is_string($b[$key])) { tlga_fail('Invalid '.$key); }
    $v = sanitize_textarea_field($b[$key] ?? '');
    if (mb_strlen($v)>$max || ($required && $v==='')) { tlga_fail('Please check '.$key); }
    return $v;
}
function tlga_permission($r) {
    $route = substr($r->get_route(),strlen('/tlg/v1')); $m = $r->get_method();
    if ($route === '/stripe/webhook') { return true; }
    if (!in_array($m,array('GET','HEAD'),true)) {
        $origin = $r->get_header('origin'); $expected = wp_parse_url(home_url()); $got = wp_parse_url($origin);
        if (!$origin || !$got || ($got['scheme']??'')!==($expected['scheme']??'') || ($got['host']??'')!==($expected['host']??'') || ($got['port']??0)!==($expected['port']??0)) {
            return new WP_Error('tlga_origin','Please use this website to submit your request.',array('status'=>403));
        }
        if (!wp_verify_nonce($r->get_header('x-wp-nonce'),'wp_rest')) {
            return new WP_Error('tlga_nonce','Your session needs refreshing. Reload this page.',array('status'=>403));
        }
    }
    $public = ($m==='GET' && preg_match('#^/(verses|sharing|endorsements|pages/(about|contact))$#',$route)) ||
      ($m==='POST' && preg_match('#^/auth/(login|register|forgot-password|reset-password)$#',$route));
    if (!$public && !is_user_logged_in()) { return new WP_Error('tlga_auth','Please sign in.',array('status'=>401)); }
    if (strpos($route,'/admin/')===0 && !current_user_can('manage_options')) { return new WP_Error('tlga_admin','Administrators only.',array('status'=>403)); }
    return true;
}
function tlga_routes() {
    $routes = array(
      '/auth/(?P<action>register|login|logout|refresh|forgot-password|reset-password|change-password)'=>'POST',
      '/auth/me'=>'GET', '/account/password'=>'POST', '/account'=>'PUT', '/account/invites'=>'GET', '/share-events'=>'POST', '/sharing/event'=>'POST',
      '/verses'=>'GET','/sharing'=>'GET','/endorsements'=>'GET','/pages/(?P<slug>about|contact)'=>'GET',
      '/admin/(?P<setting>verses|sharing|endorsements|videos)'=>'PUT', '/admin/pages/(?P<slug>about|contact)'=>'PUT',
      '/admin/codes'=>'GET,POST', '/admin/codes/(?P<code_id>[A-Za-z0-9_-]+)'=>'PUT,DELETE', '/admin/invites'=>'GET',
      '/videos'=>'GET', '/assessments'=>'GET', '/assessments/(?P<aid>[1-7])'=>'GET',
      '/assessments/(?P<aid>[1-7])/progress'=>'PUT', '/assessments/(?P<aid>[1-7])/submit'=>'POST',
      '/assessments/(?P<aid>[1-7])/result'=>'GET', '/assessments/7/video-watched'=>'POST',
      '/master-results'=>'GET','/master-results/scorecard'=>'GET', '/payments/(?P<pay_action>quote|checkout)'=>'POST',
      '/payments/status/(?P<session_id>cs_[A-Za-z0-9_]+)'=>'GET', '/stripe/webhook'=>'POST'
    );
    foreach ($routes as $path=>$methods) {
      register_rest_route('tlg/v1',$path,array('methods'=>$methods,'callback'=>'tlga_dispatch','permission_callback'=>'tlga_permission'));
    }
}
function tlga_dispatch($r) {
    try {
      $path = substr($r->get_route(),strlen('/tlg/v1')); $body = tlga_body($r);
      if (strpos($path,'/auth/')===0 || strpos($path,'/account')===0 || $path==='/sharing/event' || $path==='/share-events') { $data=tlga_accounts($path,$r,$body); }
      elseif (strpos($path,'/assessments')===0 || strpos($path,'/master-results')===0) { $data=tlga_assessments($path,$r,$body); }
      else { $data=tlga_content_payments($path,$r,$body); }
      return rest_ensure_response($data);
    } catch (TLGA_Exception $e) { return new WP_Error('tlga_request',$e->getMessage(),array('status'=>$e->getCode()?:400)); }
}
function tlga_admin_screen() {
    if (!current_user_can('manage_options')) { return; }
    echo '<div class="wrap"><h1>The Lord’s Gym</h1><p>Manage your training site using the links below.</p><ul>';
    foreach (array('verses'=>'Scripture banner','sharing'=>'Book and sharing','videos'=>'Training videos','codes'=>'Access codes','endorsements'=>'Endorsements','invites'=>'Referral statistics','pages/about'=>'About page','pages/contact'=>'Contact page') as $slug=>$label) {
      echo '<li><a href="'.esc_url(home_url('/admin/'.$slug)).'">'.esc_html($label).'</a></li>';
    }
    echo '</ul><h2>Integration status</h2><p>Stripe: '.(tlga_config('TLG_STRIPE_SECRET_KEY')?'Configured':'Not configured').'<br>Google sign-in: '.(tlga_config('TLG_GOOGLE_CLIENT_ID') && tlga_config('TLG_GOOGLE_CLIENT_SECRET')?'Configured':'Not configured').'<br>Brevo: '.(tlga_config('TLG_BREVO_API_KEY')?'Configured':'WordPress email fallback').'</p><p>Webhook endpoint: <code>'.esc_html(rest_url('tlg/v1/stripe/webhook')).'</code></p></div>';
}