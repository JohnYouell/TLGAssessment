<?php
if (!defined('ABSPATH')) { exit; }
function tlga_queue_email($kind,$uid,$attempt=0) {
    $args=array($kind,(int)$uid,(int)$attempt); if(!wp_next_scheduled('tlga_email_job',$args)) { wp_schedule_single_event(time()+5,'tlga_email_job',$args); }
}
function tlga_email_html($name,$title,$body,$button,$url) {
    return '<!doctype html><html><body style="margin:0;background:#0a0a0a;color:#fff;font-family:Arial,sans-serif"><div style="max-width:620px;margin:auto;padding:36px 24px"><img src="'.esc_url(tlga_asset('email-logo-gold.png')).'" alt="The Lord’s Gym" width="90"><h1 style="color:#d4af37">'.esc_html($title).'</h1><p>Hello '.esc_html($name).',</p><p style="line-height:1.7">'.esc_html($body).'</p><p style="margin:32px 0"><a href="'.esc_url($url).'" style="background:#d4af37;color:#000;text-decoration:none;padding:15px 24px;font-weight:bold">'.esc_html($button).'</a></p><hr style="border:0;border-top:1px solid #333"><p style="font-size:12px;color:#ccc">The Lord’s Gym · Discipleship Training, One Rep at a Time<br><a style="color:#d4af37" href="'.esc_url(home_url('/account')).'">Manage your email preferences</a></p></div></body></html>';
}
function tlga_send_mail($to,$subject,$html,$attachment=null) {
    $key=tlga_config('TLG_BREVO_API_KEY');
    if($key) {
      $payload=array('sender'=>array('name'=>"The Lord's Gym",'email'=>tlga_config('TLG_EMAIL_FROM',get_option('admin_email'))),'to'=>array(array('email'=>$to)),'subject'=>$subject,'htmlContent'=>$html);
      if($attachment) { $payload['attachment']=array(array('name'=>'Lords-Gym-Training-Scorecard.pdf','content'=>base64_encode($attachment))); }
      $r=wp_remote_post('https://api.brevo.com/v3/smtp/email',array('timeout'=>20,'headers'=>array('api-key'=>$key,'Content-Type'=>'application/json'),'body'=>wp_json_encode($payload)));
      return !is_wp_error($r) && wp_remote_retrieve_response_code($r)>=200 && wp_remote_retrieve_response_code($r)<300;
    }
    $files=array(); if($attachment) { if(!function_exists('wp_tempnam')) { require_once ABSPATH.'wp-admin/includes/file.php'; } $tmp=wp_tempnam('Lords-Gym-Training-Scorecard.pdf'); if($tmp) { $pdf_path=$tmp.'.pdf'; if(!rename($tmp,$pdf_path)) { wp_delete_file($tmp); return false; } $tmp=$pdf_path; if(file_put_contents($tmp,$attachment)===false) { wp_delete_file($tmp); return false; } $files[]=$tmp; } }
    $ok=wp_mail($to,$subject,$html,array('Content-Type: text/html; charset=UTF-8'),$files); foreach($files as $file) { wp_delete_file($file); } return $ok;
}
function tlga_email_job($kind,$uid,$attempt=0) {
    $u=get_userdata($uid); if(!$u) { return; }
    if(in_array($kind,array('reminder','nudge'),true) && metadata_exists('user',$uid,'tlga_reminders') && !(bool)get_user_meta($uid,'tlga_reminders',true)) { return; }
    $copy=array(
      'welcome'=>array('Welcome to the Training Floor','Start with your Initial Spiritual Assessment and build your spiritual strength one rep at a time.','Start Rep One','/dashboard'),
      'reminder'=>array('Ready for your first rep?','Your Initial Spiritual Assessment is waiting. Take a few minutes to establish your Day 1 baseline.','Finish Your First Rep','/assessment/1'),
      'nudge'=>array('Your next rep is waiting','You have already started the work. Return to the training floor and take your next step.','Return to Training','/dashboard'),
      'completion'=>array('Course Completed. You Finished the Work!','You completed all seven assessments. Review how you have grown and download your training scorecard.','View Your Results','/master-results'),
      'scorecard'=>array('Your Training Scorecard','Your personal training scorecard is attached. Keep it as a record of your growth.','View Your Results','/master-results')
    ); if(!isset($copy[$kind])) { return; } $c=$copy[$kind]; $attachment=null;
    if($kind==='scorecard') { try { $attachment=tlga_pdf(tlga_master($uid),$u->display_name); } catch(TLGA_Exception $e) { return; } }
    $ok=tlga_send_mail($u->user_email,$c[0],tlga_email_html($u->display_name,$c[0],$c[1],$c[2],home_url($c[3])),$attachment);
    if(!$ok && $attempt<2) { $args=array($kind,(int)$uid,$attempt+1); wp_schedule_single_event(time()+900,'tlga_email_job',$args); }
}
add_action('tlga_marketing_sync',function($uid) {
    $key=tlga_config('TLG_BREVO_API_KEY'); $list=(int)tlga_config('TLG_BREVO_LIST_ID',3); $u=get_userdata($uid); if(!$key || !$u) { return; }
    $opt=(bool)get_user_meta($uid,'tlga_marketing',true); $name=preg_split('/\s+/',$u->display_name,2);
    $payload=$opt?array('email'=>$u->user_email,'attributes'=>array('FIRSTNAME'=>$name[0],'LASTNAME'=>$name[1]??'','OPT_IN'=>true),'listIds'=>array($list),'updateEnabled'=>true):array('emails'=>array($u->user_email));
    wp_remote_post($opt?'https://api.brevo.com/v3/contacts':'https://api.brevo.com/v3/contacts/lists/'.$list.'/contacts/remove',array('timeout'=>20,'headers'=>array('api-key'=>$key,'Content-Type'=>'application/json'),'body'=>wp_json_encode($payload)));
});
function tlga_reminders() {
    $offset=(int)get_option('tlga_reminder_offset',0); $users=get_users(array('meta_key'=>'tlga_member','meta_value'=>1,'number'=>100,'offset'=>$offset,'orderby'=>'ID','order'=>'ASC'));
    foreach($users as $u) {
      if(metadata_exists('user',$u->ID,'tlga_reminders') && !(bool)get_user_meta($u->ID,'tlga_reminders',true)) { continue; } $p=tlga_progress($u->ID); $age=time()-strtotime($u->user_registered.' UTC'); $completed=0;
      foreach($p as $v) { if($v['status']==='completed') { $completed++; } }
      if($age>=48*HOUR_IN_SECONDS && !tlga_done($p,1) && add_user_meta($u->ID,'tlga_day2_sent',time(),true)) { tlga_queue_email('reminder',$u->ID); }
      $activity=(int)get_user_meta($u->ID,'tlga_activity',true);
      if($completed>0 && $completed<7 && $activity && time()-$activity>=7*DAY_IN_SECONDS && add_user_meta($u->ID,'tlga_nudge_sent',time(),true)) { tlga_queue_email('nudge',$u->ID); }
    }
    update_option('tlga_reminder_offset',count($users)===100?$offset+100:0,false);
}
function tlga_pdf($data,$name) {
    require_once TLGA_DIR.'vendor/autoload.php';
    $options=new \Dompdf\Options(); $options->set('isRemoteEnabled',false); $options->set('isPhpEnabled',false); $options->set('isJavascriptEnabled',false); $options->set('chroot',TLGA_DIR); $options->set('defaultFont','DejaVu Sans');
    $cache=get_temp_dir().'tlg-pdf-fonts'; wp_mkdir_p($cache); $options->set('fontCache',$cache); $options->set('tempDir',get_temp_dir());
    $html='<!doctype html><html><head><meta charset="UTF-8"><style>@page{margin:32pt}body{font-family:"DejaVu Sans",sans-serif;color:#1b1b1b;font-size:9pt;line-height:1.3}.masthead{background:#0a0a0a;color:#fff;padding:14pt;border-bottom:4pt solid #d4af37}.masthead h1{font-size:21pt;letter-spacing:1pt;margin:0 0 4pt}.masthead p{margin:0;font-size:10pt}.name{font-size:15pt;margin:16pt 0 3pt}.date{color:#555;margin:0 0 12pt}h2{font-size:12pt;color:#806314;margin:14pt 0 8pt}table{border-collapse:collapse;width:100%;table-layout:fixed}th,td{padding:6pt 6pt;text-align:left;border-bottom:1pt solid #e5e5e5;font-size:8pt;vertical-align:middle}th{background:#eeeeee;font-size:8pt}td.number,th.number{text-align:right}.total td{background:#f4ecd2;font-weight:bold}.change{color:#66500b}.designation{margin-top:14pt;border-left:3pt solid #d4af37;padding-left:12pt}.designation h2{margin:0 0 5pt;font-size:14pt}.footer{position:fixed;bottom:0;font-size:7pt;color:#666}</style></head><body><div class="masthead"><h1>THE LORD’S GYM</h1><p>Discipleship Training, One Rep at a Time</p></div><p class="name">'.esc_html($name).'</p><p class="date">Training Scorecard | '.esc_html(wp_date('F j, Y')).'</p><h2>YOUR GROWTH: DAY 1 TO TODAY</h2><table><thead><tr><th style="width:38%">Section</th><th style="width:20%">Chapters</th><th class="number" style="width:14%">Day 1</th><th class="number" style="width:14%">Today</th><th class="number" style="width:14%">Change</th></tr></thead><tbody>';
    foreach($data['rows'] as $r) { $html.='<tr><td>'.esc_html($r['section']).'</td><td>'.esc_html($r['chapters']).'</td><td class="number">'.(int)$r['day1'].' / 25</td><td class="number">'.(int)$r['today'].' / 25</td><td class="number change">'.($r['change']>0?'+':'').(int)$r['change'].'</td></tr>'; }
    $t=$data['total']; $html.='<tr class="total"><td colspan="2">TOTAL OUT OF 125</td><td class="number">'.(int)$t['day1'].' / 125</td><td class="number">'.(int)$t['today'].' / 125</td><td class="number">'.($t['change']>0?'+':'').(int)$t['change'].'</td></tr></tbody></table><h2>SECTION REVIEW RESULTS</h2><table><tbody>';
    foreach($data['reviews'] as $r) { $html.='<tr><td style="width:40%">'.esc_html($r['title']).'</td><td class="number" style="width:20%">'.(int)$r['score'].' / '.(int)$r['max'].'</td><td style="width:40%">'.esc_html($r['designation']).'</td></tr>'; }
    $tier=tlga_tier(tlga_assessment(7)['total_tiers'],$t['today']); $html.='</tbody></table><div class="designation"><h2>'.esc_html($tier['label']).'</h2><p>'.esc_html($tier['meaning']).'</p></div><p class="footer">A personal reflection tool for growth in Christ. Keep training, one rep at a time.</p></body></html>';
    $pdf=new \Dompdf\Dompdf($options); $pdf->setPaper('letter','portrait'); $pdf->loadHtml($html,'UTF-8'); $pdf->render(); return $pdf->output();
}
function tlga_download_scorecard($data) {
    $uid=get_current_user_id(); tlga_rate('scorecard:'.$uid,4,5*MINUTE_IN_SECONDS); $pdf=tlga_pdf($data,wp_get_current_user()->display_name); tlga_queue_email('scorecard',$uid);
    nocache_headers(); header('Content-Type: application/pdf'); header('Content-Disposition: attachment; filename="Lords-Gym-Training-Scorecard.pdf"'); header('Content-Length: '.strlen($pdf)); echo $pdf; exit;
}