<?php
/**
 * Plugin Name: The Lord's Gym Assessments
 * Description: Seven assessments, private progress, results, access codes, Stripe, and training administration.
 * Version: 1.0.1
 * Requires at least: 6.6
 * Requires PHP: 7.4
 * Author: John Youell
 */
if (!defined('ABSPATH')) { exit; }
define('TLGA_DIR', plugin_dir_path(__FILE__));
define('TLGA_VERSION', '1.0.1');
require_once TLGA_DIR . 'includes/core.php';
require_once TLGA_DIR . 'includes/assessments.php';
require_once TLGA_DIR . 'includes/accounts.php';
require_once TLGA_DIR . 'includes/content-payments.php';
require_once TLGA_DIR . 'includes/email-pdf.php';
register_activation_hook(__FILE__, 'tlga_activate');
register_deactivation_hook(__FILE__, function () { wp_clear_scheduled_hook('tlga_hourly'); flush_rewrite_rules(); });
add_action('init', 'tlga_rewrites');
add_filter('query_vars', function ($v) { $v[] = 'tlg_route'; return $v; });
add_action('rest_api_init', 'tlga_routes');
add_action('tlga_hourly', 'tlga_reminders');
add_action('tlga_email_job', 'tlga_email_job', 10, 3);
add_action('template_redirect', 'tlga_oauth');
add_action('admin_menu', function () {
    add_menu_page("The Lord's Gym", "The Lord's Gym", 'manage_options', 'tlg-training', 'tlga_admin_screen', 'dashicons-awards', 26);
});
add_action('template_redirect', function () {
    if (get_stylesheet() === 'tlg-training') {
        if (!defined('DONOTCACHEPAGE')) { define('DONOTCACHEPAGE', true); }
        nocache_headers();
        header('Referrer-Policy: strict-origin-when-cross-origin');
        header('X-Content-Type-Options: nosniff');
    }
}, 0);
add_filter('show_admin_bar', function ($show) { return get_stylesheet() === 'tlg-training' && !is_admin() ? false : $show; });
add_filter('rest_post_dispatch', function ($response, $server, $request) {
    if (strpos($request->get_route(), '/tlg/v1/') === 0) {
        $response->header('Cache-Control', 'no-store, private');
        $response->header('X-WP-Nonce', wp_create_nonce('wp_rest'));
    }
    return $response;
}, 10, 3);