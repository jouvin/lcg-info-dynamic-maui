#!/usr/bin/perl -w
use strict;

use FindBin;
use File::Basename;


my @output;      	 # ldif output that is sent to std out.
my @ldif_file;   	 # Content of the static ldif file
my @dn;          	 # A dn found in the static ldif file (lcg-info-static.ldif).
my @diagQ;	     	 # Contains the name of each queue
my @diagResults; 	 # Contains the results for CPU informations
my @nbProcList;  	 # Contains the list of queues with their number of PROC
my %nbProcList;  	 # Contains the number of Proc associate to each queue
my $pbsHost;
my $qParser;
my $queue;
my $qNames;
my $TotalCPU;
my $FreeCPU;
my $Version;
my $WallTime;
my $MaxRunningJobs;
my $Started;
my $Enabled;
my $state;
my $num_pro;
my $Status;
my $diagResult;
my $nbProc;
my $queueProcList;
my $queueName;
my $nbPQueue;
my $nbRunningJobs;

# convert triplet hours:minutes:seconds into seconds
sub convertHhMmSs {
	return $1 * 3600 + $2 * 60 + $3   if   $_[0] =~ /(\d+):(\d+):(\d+)/;

	return ($_[0] ne "-") ? $_[0] : 0;
}

if ($ARGV[0]) {
    #Reads the ldif file.
    open (LDIF, $ARGV[0]) || die "Cannot open '$ARGV[0]': $!,";
    while (<LDIF>) {
	push @ldif_file, $_;
    }
    close (LDIF);
    if($ARGV[1]){
	$pbsHost = $ARGV[1];
    }else{
	$pbsHost = `hostname -f`;
    }
} else {
    print "Usage: $0 <ldif file> [pbs host]\n";
    exit 1
}

# gets the dns containing the keyword GlueVOViewLocalID or GlueCEUniqueID
# and put this dn in @dn
for (@ldif_file) {
  if ( /dn:\s+GlueCEUniqueID=/ ) {
    push @dn, $_;
  }
}

# Get LRMS version
open QSTAT, "qstat -B -f $pbsHost 2>&1 |" or die "Error running qstat.\n";
while(<QSTAT>) {
    if ( /pbs_version\s+=\s+(\S+)/ ){
	$Version=$1;
    }
}
close QSTAT;
$Version || die "Can not obtain pbs version from host\n";

# Get Total and Free CPUs
open QSTAT, "pbsnodes -a -s  $pbsHost 2>&1 |" or die "Error running qstat.\\n";
$TotalCPU = 0;
while(<QSTAT>) {
  if ( /state = (.*)/ ) {
    $state = $1;
  }
  if( /np =/ ){
    $num_pro = $_;
    $num_pro =~ s/^[^=]*=//;
    chomp $num_pro;
    if ($state !~ /down|offline/){
      $TotalCPU += $num_pro;
    }
  }
}
close QSTAT;

#Gives the name of each queue in a string
for (@dn) {
	$qParser = $_;
	$qParser =~ s/,.*//;
	$qParser =~ s/^.*-//;
	chomp $qParser;
	push @diagQ, $qParser;
}
$qNames = join(":",@diagQ);

#Get Real Number of running jobs
my $python_exec_dir = '/opt/lcg/libexec';
$ENV{'LIBEXECPATH'} = $python_exec_dir;
open OBJ, "python $python_exec_dir/lrmsinfo-pbs | grep running |" or die " Error running lrmsinfo.\\n";
$nbRunningJobs = 0;
while( <OBJ> ) {
	$nbRunningJobs = $nbRunningJobs + 1;
 }
close OBJ;
print "nbRunningJobs = $nbRunningJobs\n";
#Get Real Number of CPU
#my $python_modules_dir = $FindBin::Bin.'/../lib/python';
my $python_modules_dir = '/opt/lcg/lib/python';
$ENV{'PYTHONPATH'} = $python_modules_dir;
open OBJ, "python $python_modules_dir/diagParserLaunch -h $pbsHost -i $qNames|" or die "Error running parser.\\n";
while( <OBJ> ) {
	$diagResult = $_;
	push @diagResults, $diagResult;
 }
close OBJ;

$nbProc = $diagResults[0];
$queueProcList = $diagResults[1];
@nbProcList = split(/,/, $queueProcList);
%nbProcList = @nbProcList;

#Gives the number of free CPU for normal jobs
$TotalCPU -= $nbProc;
#print "nb cpu ss proc : $TotalCPU\n";

# Print appropriate information concerning a pbs queue
# Queue name obtained based on each entry of @dn
for (@dn) {
  push @output, $_;
  $queue = $_;

    # The entry contains keyword GlueCEUniqueID
    $queue =~ s/,.*//;
    $queue =~ s/^.*-//;
    chomp $queue;
	$nbPQueue = 0;
	$FreeCPU = 0;
    foreach $queueName (keys %nbProcList) {
		if ($queueName eq $queue) {
			$nbPQueue = $nbProcList{$queueName};
		}	
	}

	$TotalCPU += $nbPQueue;
    $FreeCPU = $TotalCPU - $nbRunningJobs;
    if ( $FreeCPU < 0 ) {
    	$FreeCPU = 0;
    }
    push @output, "GlueCEInfoLRMSVersion: $Version\n";
    push @output, "GlueCEInfoTotalCPUs: $TotalCPU\n";
    push @output, "GlueCEStateFreeCPUs: $FreeCPU\n";

#	print "GlueCEInfoLRMSVersion: $Version\n";
#	print "GlueCEInfoTotalCPUs: $TotalCPU\n";
#	print "GlueCEStateFreeCPUs: $FreeCPU\n\n";
	
    $TotalCPU -= $nbPQueue;

  # Get the value of the following attributes:
  # GlueCEPolicyMaxCPUTime, GlueCEPolicyMaxTotalJobs, GlueCEPolicyPriority, 
  # GlueCEPolicyMaxRunningJobs, GlueCEPolicyMaxWallClockTime, GlueCEStateStatus
  $MaxRunningJobs = 9999999;
  open QSTAT, "qstat -Q -f $queue\@$pbsHost 2>&1 |" or die "Error running qstat.\n";
  $Enabled = 0;
  $Started = 0;

  while(<QSTAT>) {
    if ( /^\s+resources_max.cput\s+=\s+(\S+)/ ) {
      push @output, "GlueCEPolicyMaxCPUTime: ". int(&convertHhMmSs($1)/60) . "\n";
    }
    if ( /^\s+max_queuable\s+=\s+(\S+)/ ) {
      push @output, "GlueCEPolicyMaxTotalJobs: ". $1 . "\n";
    }
    if (/^\s+Priority\s+=\s+(\S+)/){
      push @output, "GlueCEPolicyPriority: ". $1 . "\n";
    }
    if ( /^\s+max_running\s+=\s+(\d+)/ ) {
      $MaxRunningJobs = $1 if ($1);
      push @output, "GlueCEPolicyMaxRunningJobs: " . int($1) . "\n";
    }
    if ( /^\s+resources_max.walltime\s+=\s+(\S+)/ ) {
      $WallTime = &convertHhMmSs($1);
      push @output, "GlueCEPolicyMaxWallClockTime: ". int($WallTime/60) . "\n";
    }
    if ( /^\s+enabled\s+=\s+(True)/ ) {
      $Enabled = 1;
    }
    if ( /^\s+started\s+=\s+(True)/ ) {
      $Started = 1;
    }
  }
  close QSTAT;

  $Status =
    ($Enabled && $Started) ? "Production" :
      ($Enabled) ? "Queueing" :
	($Started) ? "Draining" : "Closed" ;
  push @output, "GlueCEStateStatus: $Status\n";
  push @output, "\n";
}

#print @output;

exit;
