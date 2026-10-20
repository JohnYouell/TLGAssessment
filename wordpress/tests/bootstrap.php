<?php
// Real WordPress and MySQL; all mail and provider HTTP requests are intercepted.
$wordpress=getenv('TLG_WP_DIR');
if(!$wordpress || !is_file($wordpress.'/wp-settings.php')) { throw new RuntimeException('TLG_WP_DIR must point to a disposable WordPress installation.'); }
define('ABSPATH',rtrim($wordpress,'/').'/');
define('DB_NAME','tlgtest'); define('DB_USER','root'); define('DB_PASSWORD','tlg-test-only');
define('DB_HOST','127.0.0.1:3306'); define('DB_CHARSET','utf8mb4'); define('DB_COLLATE','');
define('WP_INSTALLING',true); define('DISABLE_WP_CRON',true);
define('WP_DEBUG',false); define('WP_DEBUG_DISPLAY',false); define('WP_DISABLE_FATAL_ERROR_HANDLER',true);
define('WP_HOME','https://tlg.example.test'); define('WP_SITEURL','https://tlg.example.test');
define('AUTH_KEY','tlg-test-auth'); define('SECURE_AUTH_KEY','tlg-test-secure');
define('LOGGED_IN_KEY','tlg-test-logged-in'); define('NONCE_KEY','tlg-test-nonce');
define('AUTH_SALT','tlg-test-auth-salt'); define('SECURE_AUTH_SALT','tlg-test-secure-salt');
define('LOGGED_IN_SALT','tlg-test-login-salt'); define('NONCE_SALT','tlg-test-nonce-salt');
define('TLG_STRIPE_SECRET_KEY','rk_test_fixture_not_a_credential');
define('TLG_STRIPE_WEBHOOK_SECRET','whsec_fixture_not_a_credential');
$table_prefix='wp_'; $_SERVER['HTTP_HOST']='tlg.example.test'; $_SERVER['REQUEST_METHOD']='GET';
require ABSPATH.'wp-settings.php';
add_filter('pre_wp_mail','__return_true');
add_filter('pre_http_request',function($pre,$args,$url) {
    if(strpos($url,'https://api.stripe.com/v1/')!==0) { return new WP_Error('fixture_network_blocked','External HTTP is blocked in tests.'); }
    return tlg_fixture_stripe($args,substr($url,strlen('https://api.stripe.com/v1/')));
},10,3);
require_once ABSPATH.'wp-admin/includes/upgrade.php';
wp_install('TLG regression fixture','fixture-admin','admin@example.invalid',false,'','test-only-password-12345');
require dirname(__DIR__).'/tlg-assessments/tlg-assessments.php';
tlga_activate();
$GLOBALS['wpdb']->suppress_errors(true);
