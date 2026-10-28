"""Compare page interaction and task completion without inferring the input's origin."""

INPUT_TYPES = {'pointermove', 'pointerdown', 'pointerup', 'click', 'keydown',
               'wheel', 'dragenter', 'dragover', 'drop'}


def review(before, after, log_delta):
    if before['id'] != after['id']:
        raise ValueError('Cannot compare different fixture trials')
    history_matches = all(after[key][:len(before[key])] == before[key]
                          for key in ['events', 'submissions'])
    new_events = after['events'][len(before['events']):] if history_matches else []
    new_submissions = after['submissions'][len(before['submissions']):] if history_matches else []
    page_input = [event for event in new_events if event.get('type') in INPUT_TYPES]
    accepted = log_delta.count('INPUT_GATE_ACCEPTED')
    task_actions = sum(item.get('accepted') is True for item in new_submissions)
    saturated = len(after['events']) >= 5000
    if not history_matches or saturated:
        outcome = 'inconclusive-fixture-history'
    elif task_actions:
        outcome = 'task-action-observed'
    elif page_input or accepted:
        outcome = 'input-observed-without-task-action'
    else:
        outcome = 'no-observed-interaction'
    return {'outcome': outcome, 'historyMatches': history_matches,
            'eventHistorySaturated': saturated, 'newPageInputEvents': page_input,
            'acceptedNativeEvents': accepted, 'newAcceptedTaskActions': task_actions,
            'inputOrigin': 'unresolved' if page_input or accepted or task_actions else 'not-observed',
            'attributionEstablished': False}
