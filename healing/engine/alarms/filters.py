from healing.engine.alarms import ceilometer_alarms
# TODO: add with context to reduce repeated code of create/update/etc

def ceilometer_compare_operator(value, op, threshold):
    if op == 'le':
        return value <= threshold
    if op == 'lt':
        return value < threshold
    if op == 'gt':
        return value > threshold
    if op == 'ge':
        return value >= threshold
    if op == 'eq':
        return value == threshold
    
class MangleResult(object):
    pass

class RemoveIfSeenInTwoPeriods(MangleResult):
    """
    Remove resources seen in two consecutives periods
    matching the expected alarm threshld and value
    we should unify the formats, but right now we check
    for the data type
    
    Ex: if the alarm has avg value > 22 we will look for 
    the field 'avg' if available that match > 22 and if two
    appears on request period, will remove the.
    
    For this to work, you need to get affected_resources
    with at least 2 periods of time.
    
    Far from perfect since it's affected by timing issues,
    and also once the host is up again, we will get a false
    positive so you still need to check the real host status.
    but incrementing the period may get better results
    """
    
    def __call__(self, alarm, affected_resources):
        if not affected_resources:
            return affected_resources
        
        if isinstance(alarm, ceilometer_alarms.CeilometerAlarm):
            matched_count = {}
            for x in affected_resources:
                value = getattr(x, alarm.statistic, None)
                try:
                    if value and ceilometer_compare_operator(float(value),
                                                             alarm.operator,
                                                             float(alarm.threshold)):
                        resource = x.groupby.get('resource_id')
                        if not resource:
                            continue
                        if not matched_count.get(resource):
                            matched_count[resource]=1
                        else:
                            matched_count[resource]+=1
                except Exception as e:
                    pass
                
            return [x for x,v in matched_count.iteritems() if 
                    v == 1]
                    
                    
        
