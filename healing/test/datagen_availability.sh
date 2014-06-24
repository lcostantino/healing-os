
#!/bin/bash


##################
#SetUp
##################

keystone_url=http://127.0.0.1:5000/v2.0/

export OS_AUTH_URL=$keystone_url


##################
#Generating vms
##################

vm1_name=test$RANDOM
echo 'vm1 name:' $vm1_name
vm2_name=test$RANDOM
echo 'vm2 name:' $vm2_name
vm3_name=test$RANDOM
echo 'vm3 name:' $vm3_name

host_name=$(nova host-list | grep -m 1 -o '.* | compute .*' | awk '{ print $2 }')
echo 'host name:' $host_name

uuid_pattern='[0-9a-fA-F]\{8\}-[0-9a-fA-F]\{4\}-[0-9a-fA-F]\{4\}-[0-9a-fA-F]\{4\}-[0-9a-fA-F]\{12\}'
image='cirros-0.3.2-x86_64-uec'

vm1_id=$(nova boot --flavor m1.tiny --image $image $vm1_name | grep '| id .*| ' | grep -o $uuid_pattern)
echo 'vm1 id:' $vm1_id

vm2_id=$(nova boot --flavor m1.tiny --image $image $vm2_name | grep '| id .*| ' | grep -o $uuid_pattern)
echo 'vm2 id:' $vm2_id

vm3_id=$(nova boot --flavor m1.tiny --image $image $vm3_name | grep '| id .*| ' | grep -o $uuid_pattern)
echo 'vm3 id:' $vm3_id

####################################################
#Generating ceilometer samples for instance meter
####################################################

date_format=%Y-%m-%dT%H:%M:%S
start_date=$(date -I)T01:00:00 
start_date_sec=$(date -d $start_date +%s)
end_date=$(date -I)T15:00:00
end_date_sec=$(date -d $end_date +%s)
iter_date=$start_date_sec
period=300
samplevolume=1
meter=instance
meterunit=instance
metertype=gauge

vms_array=( $vm1_id $vm2_id $vm3_id )
for vm in "${vms_array[@]}"
do	
	while [ $iter_date -le $end_date_sec ]
	do
		formated_iter_date=$(date -d @$iter_date +$date_format)	
		ceilometer sample-create -m $meter --meter-unit $meterunit --sample-volume $samplevolume -r $host_name --resource-id $vm --meter-type $metertype --timestamp $formated_iter_date
		iter_date=$(($iter_date+$period))
	done
done

###############################################
#Generating ceilometer samples for cpu meter
###############################################

meter=cpu
meterunit=cpu
metertype=cumulative

first_host_down_date=$(date -I)T02:00:00 
first_host_down_date_sec=$(date -d $first_host_down_date +%s)
first_up_vm1_date=$(date -I)T02:10:00 
first_up_vm1_date_sec=$(date -d $first_up_vm1_date +%s)
first_up_vm2_date=$(date -I)T02:20:00 
first_up_vm2_date_sec=$(date -d $first_up_vm2_date +%s)
first_up_vm3_date=$(date -I)T02:00:00 
first_up_vm3_date_sec=$(date -d $first_up_vm3_date +%s)

second_host_down_date=$(date -I)T10:00:00 
second_host_down_date_sec=$(date -d $second_host_down_date +%s)
second_up_vm1_date=$(date -I)T10:16:00 
second_up_vm1_date_sec=$(date -d $second_up_vm1_date +%s)
second_up_vm2_date=$(date -I)T10:20:00 
second_up_vm2_date_sec=$(date -d $second_up_vm2_date +%s)
second_up_vm3_date=$(date -I)T10:06:00 
second_up_vm3_date_sec=$(date -d $second_up_vm3_date +%s)

vms_array=( $vm1_id $vm2_id $vm3_id )
first_up_date=( $first_up_vm1_date_sec $first_up_vm2_date_sec $first_up_vm3_date_sec )
second_up_date=( $second_up_vm1_date_sec $second_up_vm2_date_sec $second_up_vm3_date_sec )


vms_array=( $vm1_id $vm2_id $vm3_id )
for i in 0 1 2
do	
	vm=${vms_array[$i]}

	iter_date=$start_date_sec
	while [ $iter_date -le $first_host_down_date_sec ]
	do
		formated_iter_date=$(date -d @$iter_date +$date_format)	
		ceilometer sample-create -m $meter --meter-unit $meterunit --sample-volume $samplevolume -r $host_name --resource-id $vm --meter-type $metertype --timestamp $formated_iter_date
		iter_date=$(($iter_date+$period))
	done

	iter_date=${first_up_date[$i]}
	while [ $iter_date -le $second_host_down_date_sec ]
	do
		formated_iter_date=$(date -d @$iter_date +$date_format)	
		ceilometer sample-create -m $meter --meter-unit $meterunit --sample-volume $samplevolume -r $host_name --resource-id $vm --meter-type $metertype --timestamp $formated_iter_date
		iter_date=$(($iter_date+$period))
	done

	iter_date=${second_up_date[$i]}
	while [ $iter_date -le $end_date_sec ]
	do
		formated_iter_date=$(date -d @$iter_date +$date_format)	
		ceilometer sample-create -m $meter --meter-unit $meterunit --sample-volume $samplevolume -r $host_name --resource-id $vm --meter-type $metertype --timestamp $formated_iter_date
		iter_date=$(($iter_date+$period))
	done
done


##################
#Reconfig
##################

keystone_url=http://127.0.0.1:5000/v3/

export OS_AUTH_URL=$keystone_url

#######################################
#Adding failures tracks and actions 
#######################################

alarm_id1=alarm$RANDOM
alarm_id2=alarm$RANDOM
name1=name$RANDOM
name2=name$RANDOM
name3=name$RANDOM
name4=name$RANDOM
name5=name$RANDOM
status=evacuate

healing sla-tracking-create -created_at $first_host_down_date -alarm_id $alarm_id1
id1=$(healing sla-tracking-list | grep -m 2 '| .* |' | grep -o $uuid_pattern | awk '{ print $1 }' | grep -m 1 '.*')
healing sla-tracking-create -created_at $second_host_down_date -alarm_id $alarm_id2
id2=$(healing sla-tracking-list | grep -m 2 '| .* |' | grep -o $uuid_pattern | awk '{ print $1 }' | grep -m 1 '.*')

healing sla-actions-create -name $name1 -target_id $vm1_id -request_id $id1 -status $status
healing sla-actions-create -name $name2 -target_id $vm2_id -request_id $id1 -status $status
healing sla-actions-create -name $name3 -target_id $vm1_id -request_id $id2 -status $status
healing sla-actions-create -name $name4 -target_id $vm2_id -request_id $id2 -status $status
healing sla-actions-create -name $name5 -target_id $vm3_id -request_id $id2 -status $status





