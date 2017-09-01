import os
import click

from json import dumps, loads, load
from requests import post, get

url = 'https://wintermute-151001.appspot.com'

base_dir = os.path.dirname(os.path.realpath(__file__))

for directory in ['data', 'output']:
    path = os.path.join(base_dir, directory)
    if not os.path.exists(path):
        os.makedirs(path)


def get_game_timestamp(endpoint='/game/time'):
    return round(float(get(url + endpoint).content), ndigits=0)


def get_token(uid=None, endpoint='/game/session/everwing/'):
    response = get(url + endpoint + uid)
    return loads(response.content)


def get_user_data(uid=None, endpoint='/game/state/everwing/default/'):
    response = get(url + endpoint + uid)
    return loads(response.content)


def post_to_game(user_data=None, token=None, endpoint='/game/action'):
    user_data = unicode(user_data)
    headers = {"Host": "wintermute-151001.appspot.com",
               "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0",
               "Accept": "application/json, text/plain, */*",
               "Accept-Language": "en-US,en;q=0.5",
               "Accept-Encoding": "gzip, deflate, br",
               "Content-Type": "application/json;charset=utf-8",
               "x-wintermute-session": str(token['token']),
               "Connection": "keep-alive"}

    return post(url + endpoint, data=user_data, headers=headers)


def set_max_currency(state_dict=None):
    i = 0
    for instance in state_dict['instances']:
        try:
            if instance['modelID'] == "Currency:trophy":
                instance['value'] = 99999
            if instance['modelID'] == "Currency:coin":
                instance['value'] = 99999
            state_dict['instances'][i] = instance

        except Exception as e:
            print (e)

        i += 1

    return state_dict


def set_max_characters(state_dict=None):
    character_strings = ['Item:lenore', 'Item:coin',
                         'Item:sophia', 'Item:jade',
                         'Item:arcana', 'Item:fiona',
                         'Item:standard', 'Item:magnet']
    i = 0  # index for instances
    for instance in state_dict['instances']:
        try:
            if instance['modelID'] in character_strings:
                instance['stats']['level'] = 50
                if instance['state'] == 'locked':
                    instance['state'] = 'idle'
                state_dict['instances'][i] = instance

        except Exception as e:
            print (e)

        i += 1
    return state_dict


def set_max_sidekicks(state_dict=None):
    # Criteria
    sidekick_string = 'Item:sidekick'

    i = 0  # index for instances
    for instance in state_dict['instances']:
        try:
            # Item:sidekick is the current string use for sidekicks
            if sidekick_string in instance["modelID"]:
                instance['stats']['maturity'] = 3
                instance['stats']['xp'] = 125800
                instance['stats']['zodiacBonus'] = 2
                state_dict['instances'][i] = instance
        except Exception as e:
            print (e)
        i += 1
    return state_dict


def save_user_data(uid=None, user_data=None):
    """
    FUNCTIONS TO GATHER USER DATA FOR EXAMINATION
    """
    data = user_data if user_data else get_user_data(uid)
    data = data.copy()
    uid = uid if uid else data['user_id']

    for k in data.iterkeys():
        try:
            data[k] = loads(data[k])
        except Exception as e:
            continue
    outfile = open(os.path.join(base_dir, 'data', 'user-data-{}.json'.format(uid)), 'w')
    outfile.write(dumps(data, sort_keys=True, indent=4))
    outfile.close()


def restore_user_data(uid):
    filename = 'user-data-{}.json'.format(uid)

    with open(os.path.join(base_dir, 'data', filename)) as data_file:
        restore_point = load(data_file)

    user_data = loads(get_user_data(uid))

    user_data['state'] = dumps(restore_point['state'])
    user_data['timestamp'] = get_game_timestamp()
    user_data['server_timestamp'] = get_game_timestamp()

    user_data = dumps(user_data)
    token = get_token(uid)
    resp = post_to_game(user_data, token)
    print(resp)


@click.command()
@click.option('--uid', '-u', nargs=1, type=unicode, default=None)
def start(uid):
    set_functions = []

    if uid is None:
        uid = click.prompt('Please enter your uid', type=unicode)

    if click.confirm('Do want to unlock all and max out your characters?'):
        set_functions.append(set_max_characters)

    if click.confirm('Do want to max out your currencies?'):
        set_functions.append(set_max_currency)

    if click.confirm('Do want to max out your current dragons?'):
        set_functions.append(set_max_sidekicks)

    function_names = ", ".join([i.__name__ for i in set_functions])

    click.echo('\nYou have chosen the following function/s {}'.format(function_names))
    click.echo('\nProceeding . . .\n')

    user_data = get_user_data(uid)
    save_user_data(uid, user_data)
    state_dict = loads(user_data['state'])
    
    for set_function in set_functions:
        state_dict = set_function(state_dict)

    if len(set_functions) > 0:
        user_data['state'] = dumps(state_dict)
        user_data['timestamp'] = get_game_timestamp()
        user_data['server_timestamp'] = get_game_timestamp()
        user_data = dumps(user_data)

        outfile = open(os.path.join(base_dir, 'output', 'user-data-{}.json'.format(uid)), 'w')
        outfile.write(dumps(state_dict, sort_keys=True, indent=4))
        outfile.close()

        token = get_token(uid)
        resp = post_to_game(user_data, token)
        print(resp)

    else:
        print('Nothing is selected....')


if __name__ == '__main__':
    start()
