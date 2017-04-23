#!/usr/bin/perl

use strict;
use warnings;

require LWP::UserAgent;
use POSIX qw/ceil/;

my $ua = LWP::UserAgent->new(agent => 'DorpArchive Bot');
$ua->timeout(10); 

my $sid = '';

$ua->default_header('Host' => 'archive.raytron.org');
$ua->default_header('Accept' => 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8');
$ua->default_header('Accept-Language' => 'en-us,en;q=0.5');
$ua->default_header('Accept-Encoding' => 'gzip, deflate');
$ua->default_header('DNT' => '1');
$ua->default_header('Connection' => 'keep-alive');
$ua->default_header('Cache-Control' => 'max-age=0');
#$ua->default_header();

my $max_topic_id = 941;
my $posts_per_topic_page = 30;
my $topics_per_forum_page = 50;

my $output_file_name_base = 'techtalk-';

my $base_url = 'http://archive.raytron.org/techtalk/viewtopic.php';

my %status = ();

for (my $i = 1; $i <= $max_topic_id; $i++) {
        my $posts_in_topic = 0;
        my $url = $base_url . '?sid=' .$sid . '&t='.$i;

        my $response = $ua->get($url );
        if ($response->is_success) {
                my $page_content = $response->decoded_content;
                # [ 621 posts ]
                if ($page_content =~ /topic does not exist/) {
                        print STDERR "$url: Topic $i does not exist\n";
                        $status{'invalid topic'}++;
                } elsif ($page_content =~ /not authorised/) {
                        print STDERR "$url: Not authorized\n";
                        $status{'unauthorized'}++;
                } elsif ($page_content =~ /requires you to be registered and logged in/) {
                        print STDERR "$url: Login prompt.\n";
                        $status{'login message'}++;
                } elsif ($page_content =~ /forum you selected does not exist/) {
                        print STDERR "$url: Forum does not exist\n";
                        $status{'forum dne'}++;
                } else {
                        $posts_in_topic = ($page_content =~ / ([\d,]+) post(s?) /)[0];
                        $posts_in_topic =~ s/,//;
                        $status{'valid post'}++;
#                        print "Topic #$i contains $posts_in_topic posts\n";

                        my $title = ($page_content =~ /<title>(.+)<\/title>/)[0];
                        $title =~ s/[^\w\s]+//g;
                        $title =~ s/\s+/_/g;

                        # <td class="postbottom" align="center">Sat Nov 01, 2008 9:00 pm</td>
                        my ($crap, $wd, $month, $day, $year) = ($page_content =~ />((\w{3}) (\w{3}) (\d{2}), (\d{4})) \d+:\d{2} ..<\/td/);
                        my $date_str = "$year-$month-$day";

                        my $output_filename = sprintf("$output_file_name_base"."topic-%05d.html",$i);

                        open(FILE, ">$output_filename") or die $!;
                        print FILE $page_content;
                        close(FILE);
                        print "Saved $output_filename ($posts_in_topic total posts)\n";

                        if ($posts_in_topic > $posts_per_topic_page) {
                                my $total_pages = ceil($posts_in_topic / $posts_per_topic_page);
                                for (my $j = 1; $j < $total_pages; $j++) {
                                        my $start = $j * $posts_per_topic_page;
                                        my $page_url = $url . '&start='.$start;
                                        my $page_filename = sprintf("$output_file_name_base".'topic-%05d-page-%03d.html',$i, $j);
                                        my $page_response = $ua->get($page_url, ':content_file' => $page_filename);
                                        if ($page_response->is_success) {
                                                print "Saved $page_filename\n";
                                        } else {
                                                print STDERR "Error fetching $page_url: {$response}\n";
                                        }
                                } 

                        }

                 #       print $page_content;
                }

        } else {
                print STDERR "Error fetching $url: {$response}\n";
                $status{'error:'.$response->status_line}++;
        }

}
