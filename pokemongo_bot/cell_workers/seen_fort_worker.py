import json
import time
from math import radians, sqrt, sin, cos, atan2
from pgoapi.utilities import f2i, h2f
from utils import distance, print_green, print_yellow, print_red
from pokemongo_bot.human_behaviour import sleep


class SeenFortWorker(object):

    def __init__(self, fort, bot):
        self.fort = fort
        self.api = bot.api
        self.position = bot.position
        self.config = bot.config
        self.item_list = bot.item_list
        self.rest_time = 50
        self.stepper = bot.stepper

    def work(self):
        lat = self.fort['latitude']
        lng = self.fort['longitude']

        fortID = self.fort['id']
        dist = distance(self.position[0], self.position[1], lat, lng)

        print('Found fort {} at distance {}m'.format(fortID, dist))
        if dist > 10:
            print('Need to move closer to Pokestop')
            position = (lat, lng, 0.0)

            if self.config.walk > 0:
                self.stepper._walk_to(self.config.walk, *position)
            else:
                self.api.set_position(*position)
            self.api.player_update(latitude=lat,longitude=lng)
            response_dict = self.api.call()
            print('Arrived at Pokestop')
            sleep(2)

        self.api.fort_details(fort_id=self.fort['id'], latitude=position[0], longitude=position[1])
        response_dict = self.api.call()
        fort_details = response_dict['responses']['FORT_DETAILS']
        fort_name = fort_details['name'].encode('utf8', 'replace')
        print_yellow('Now at Pokestop: ' + fort_name + ' - Spinning...')
        sleep(2)
        self.api.fort_search(fort_id=self.fort['id'], fort_latitude=lat, fort_longitude=lng, player_latitude=f2i(position[0]), player_longitude=f2i(position[1]))
        response_dict = self.api.call()
        if 'responses' in response_dict and \
            'FORT_SEARCH' in response_dict['responses']:

            spin_details = response_dict['responses']['FORT_SEARCH']
            if spin_details['result'] == 1:
                print_green("- Loot: ")
                experience_awarded = spin_details.get('experience_awarded', False)
                if experience_awarded:
                    print_green("- " + str(experience_awarded) + " xp")

                items_awarded = spin_details.get('items_awarded', False)
                if items_awarded:
                    for item in items_awarded:
                        item_id = str(item['item_id'])
                        item_name = self.item_list[item_id]
                        print_green("- " + str(item['item_count']) + "x " + item_name)
                else:
                    print_yellow("- Nothing found.")

                pokestop_cooldown = spin_details.get('cooldown_complete_timestamp_ms')
                if pokestop_cooldown:
                    seconds_since_epoch = time.time()
                    print '- PokeStop on cooldown. Time left: %s seconds.' % str((pokestop_cooldown/1000) - seconds_since_epoch)

                if not items_awarded and not experience_awarded and not pokestop_cooldown:
                    message = (
                        'Stopped at Pokestop and did not find experience, items '
                        'or information about the stop cooldown. You are '
                        'probably softbanned. Try to play on your phone, '
                        'if pokemons always ran away and you find nothing in '
                        'PokeStops you are indeed softbanned. Please try again '
                        'in a few hours.'
                    )
                    raise RuntimeError(message)
            elif spin_details['result'] == 2:
                print("- Pokestop out of range")
            elif spin_details['result'] == 3:
                pokestop_cooldown = spin_details.get('cooldown_complete_timestamp_ms')
                if pokestop_cooldown:
                    seconds_since_epoch = time.time()
                    print '- PokeStop on cooldown. Time left: %s seconds.' % str((pokestop_cooldown/1000) - seconds_since_epoch)
            elif spin_details['result'] == 4:
                print_red("- Inventory is full!")

            if 'chain_hack_sequence_number' in response_dict['responses']['FORT_SEARCH']:
                time.sleep(2)
                return response_dict['responses']['FORT_SEARCH']['chain_hack_sequence_number']
            else:
                print_yellow('may search too often, lets have a rest')
                return 11
        sleep(8)
        return 0

    @staticmethod
    def closest_fort(current_lat, current_long, forts):
        print x
