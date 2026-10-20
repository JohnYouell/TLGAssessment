<?php
if (!defined('ABSPATH')) { exit; }
function tlga_assessment($id) { foreach(tlga_data()['ASSESSMENTS'] as $a) { if($a['id']===$id) { return $a; } } tlga_fail('Assessment not found',404); }
function tlga_progress($uid = 0) {
    global $wpdb; $uid=$uid?:get_current_user_id(); $rows=$wpdb->get_results($wpdb->prepare('SELECT assessment_id,data FROM '.tlga_table('progress').' WHERE user_id=%d',$uid),ARRAY_A); $out=array();
    foreach($rows as $row) { $out[(int)$row['assessment_id']]=json_decode($row['data'],true); } return $out;
}
function tlga_done($p,$id) { return isset($p[$id]) && $p[$id]['status']==='completed'; }
function tlga_lock($a,$p,$uid = 0) {
    if ($a['tier']==='paid' && !tlga_has_access($uid)) { return 'paywall'; }
    if ($a['kind']==='final') { foreach(range(1,6) as $id) { if(!tlga_done($p,$id)) { return 'sequence'; } } }
    return null;
}
function tlga_guard($a,$p) { $lock=tlga_lock($a,$p); if($lock) { tlga_fail($lock==='paywall'?'Unlock the Full Training Program to access this.':'Complete the earlier assessments first.',$lock==='paywall'?402:403); } }
function tlga_tier($tiers,$score) { $selected=$tiers[0]; foreach($tiers as $t) { if($score >= $t['min']) { $selected=$t; } } return $selected; }
function tlga_clean_answers($a,$answers) {
    if(!is_array($answers)) { tlga_fail('Answers must be a question/value map.'); } $valid=array_column($a['questions'],'id'); $out=array();
    foreach($answers as $key=>$value) {
      if(!in_array($key,$valid,true) || !is_int($value) || $value<1 || $value>5) { tlga_fail('One or more answers are invalid.'); }
      $out[$key]=$value;
    } return $out;
}
function tlga_score($a,$answers) {
    $band=tlga_tier($a['total_tiers'],array_sum($answers)); $sections=array();
    foreach($a['questions'] as $q) { if($q['section']) { $sid=$q['section']; $sections[$sid]=($sections[$sid]??0)+$answers[$q['id']]; } }
    return array('answers'=>$answers,'status'=>'completed','score'=>array_sum($answers),'max_score'=>count($a['questions'])*5,'designation'=>$band['label'],'meaning'=>$band['meaning'],'section_scores'=>$sections,'completed_at'=>tlga_now(),'updated_at'=>tlga_now());
}
function tlga_result($a,$p) {
    $sections=array(); if($a['has_sections']) {
      foreach(tlga_data()['SECTIONS'] as $s) { $score=$p['section_scores'][$s['id']]??0; $band=tlga_tier($a['section_tiers'],$score); $sections[]=array_merge($s,array('score'=>$score,'max'=>25,'designation'=>$band['label'],'meaning'=>$band['meaning'])); }
    }
    return array_merge(array_intersect_key($a,array_flip(array('title','subtitle','kind'))),array('assessment_id'=>$a['id'],'score'=>$p['score'],'max_score'=>$p['max_score'],'designation'=>$p['designation'],'meaning'=>$p['meaning'],'completed_at'=>$p['completed_at'],'sections'=>$sections));
}
function tlga_store_progress($aid,$data) {
    global $wpdb; $uid=get_current_user_id(); $table=tlga_table('progress');
    $wpdb->query($wpdb->prepare("INSERT IGNORE INTO $table (user_id,assessment_id,status,data,updated_at) VALUES (%d,%d,'in_progress','{}',%s)",$uid,$aid,tlga_now()));
    $ok=$wpdb->query($wpdb->prepare("UPDATE $table SET data=%s,status=%s,updated_at=%s WHERE user_id=%d AND assessment_id=%d AND status <> 'completed'",wp_json_encode($data),$data['status'],tlga_now(),$uid,$aid));
    if($ok===false) { tlga_fail('Your progress could not be saved. Please try again.',500); }
    if($ok===0 && tlga_done(tlga_progress(),$aid)) { tlga_fail('Assessment already completed.'); }
}
function tlga_master($uid = 0) {
    $uid=$uid?:get_current_user_id(); $p=tlga_progress($uid);
    if(!tlga_has_access($uid)) { tlga_fail('Unlock the Full Training Program to see Master Results.',402); }
    foreach(range(1,7) as $id) { if(!tlga_done($p,$id)) { tlga_fail('Complete all 7 assessments to unlock Master Results.',403); } }
    $rows=array(); foreach(tlga_data()['SECTIONS'] as $s) {
      $d=$p[1]['section_scores'][$s['id']]; $n=$p[7]['section_scores'][$s['id']]; $rows[]=array('section'=>$s['title'],'chapters'=>$s['chapters'],'day1'=>$d,'today'=>$n,'change'=>$n-$d,'max'=>25);
    }
    $total=array('day1'=>array_sum(array_column($rows,'day1')),'today'=>array_sum(array_column($rows,'today')),'max'=>125); $total['change']=$total['today']-$total['day1'];
    $reviews=array(); foreach(range(2,6) as $id) { $a=tlga_assessment($id); $reviews[]=array('title'=>$a['title'],'chapters'=>$a['subtitle'],'score'=>$p[$id]['score'],'max'=>$p[$id]['max_score'],'designation'=>$p[$id]['designation']); }
    return array('rows'=>$rows,'total'=>$total,'reviews'=>$reviews);
}
function tlga_assessments($path,$r,$body) {
    $p=tlga_progress(); $uid=get_current_user_id();
    if($path==='/master-results') { return tlga_master(); }
    if($path==='/master-results/scorecard') { $data=tlga_master(); tlga_download_scorecard($data); }
    if($path==='/assessments') {
      $items=array(); foreach(tlga_data()['ASSESSMENTS'] as $a) { $pr=$p[$a['id']]??array(); $lock=tlga_lock($a,$p);
        $items[]=array_merge(array_intersect_key($a,array_flip(array('id','title','subtitle','description','kind','tier'))),array('question_count'=>count($a['questions']),'answered_count'=>count($pr['answers']??array()),'status'=>$pr['status']??'not_started','unlocked'=>$lock===null,'lock'=>$lock,'score'=>$pr['score']??null,'max_score'=>$pr['max_score']??null,'designation'=>$pr['designation']??null)); }
      return array('assessments'=>$items,'has_access'=>tlga_has_access(),'master_unlocked'=>tlga_has_access() && tlga_done($p,7) && tlga_done($p,1));
    }
    $aid=(int)$r['aid']; if($path==='/assessments/7/video-watched') { $aid=7; }
    $a=tlga_assessment($aid); tlga_guard($a,$p);
    if(substr($path,-7)==='/result') { if(!tlga_done($p,$aid)) { tlga_fail('Result not available yet.',404); } return tlga_result($a,$p[$aid]); }
    if($path==='/assessments/7/video-watched') { update_user_meta($uid,'tlga_final_video',1); return array('ok'=>true); }
    $video_required=$aid===7 && !get_user_meta($uid,'tlga_final_video',true);
    if($r->get_method()==='GET') {
      return array_merge(array_intersect_key($a,array_flip(array('id','title','subtitle','description','kind'))),array('video_required'=>$video_required,'questions'=>$video_required?array():$a['questions'],'sections'=>$a['has_sections']?tlga_data()['SECTIONS']:array(),'answers'=>(object)($p[$aid]['answers']??array()),'status'=>$p[$aid]['status']??'not_started'));
    }
    if($video_required) { tlga_fail('Watch the pastor’s video first.',403); }
    if(tlga_done($p,$aid)) { tlga_fail('Assessment already completed.'); }
    $answers=tlga_clean_answers($a,$body['answers']??null); $submit=substr($path,-7)==='/submit';
    if($submit && count($answers)!==count($a['questions'])) { tlga_fail('Please answer every question before submitting.'); }
    $data=$submit?tlga_score($a,$answers):array('answers'=>$answers,'status'=>'in_progress','updated_at'=>tlga_now());
    tlga_store_progress($aid,$data); tlga_touch(); if($submit && $aid===7) { tlga_queue_email('completion',$uid); }
    return $submit?tlga_result($a,$data):array('ok'=>true,'answered_count'=>count($answers));
}