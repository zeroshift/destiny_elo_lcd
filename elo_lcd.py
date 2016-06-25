#!/usr/bin/env python

import argparse
import logging
import requests
import sys
import time
import yaml
import Adafruit_CharLCD as LCD

def _get_args():
    """Get arguments and options."""
    parser = argparse.ArgumentParser(description='Raspberry Pi LCD ELO Tracking',
                                     prog='elo_lcd.py')

    parser.add_argument('-m', '--mode',
                        dest='mode', action='store', default="ToO",
                        metavar="STRING",
                        help='Set the mode. (ToO, IB, etc. Default: %(default)s)')
    parser.add_argument('-f', '--config-file',
                        dest='config_file', action='store', default="./config.yml",
                        metavar="CONFIG_FILE",
                        help='Set the location of the yaml config file to read.')
    parser.add_argument('-l', '--list-modes',
                        dest='list_modes', action='store_true', default=False,
                        help='List crucible modes.')
    parser.add_argument('--log-level',
                        dest='log', action='store', default="info",
                        metavar="LOG LEVEL",
                        help='Set the log level. (Default: %(default)s)')
    parser.add_argument('--log-file',
                        dest='log_file', action='store', default=None,
                        metavar="LOG_FILE",
                        help='Set the log file.')
    
    parser.add_argument('psn',
                        nargs=1,
                        metavar="PSN",
                        help='PSN of user to look up.')

    args = parser.parse_args()
    return args


def main():

    args = _get_args()
    # Setup Logging
    numeric_log_level = getattr(logging, args.log.upper(), None)
    if not isinstance(numeric_log_level, int):
        raise ValueError('Invalid log level: %s' % args.log)
    logging.basicConfig(level=numeric_log_level,
                        format='[%(asctime)s %(levelname)s] %(message)s',
                        datefmt='%Y%m%d %H:%M:%S',
                        filename=args.log_file)

    logging.info("[elo_lcd.py] Starting up...")

    # Start
    modes = { 523: "Crimson Doubles",
          14: "ToO",
          19: "IB",
          10: "Control",
          12: "Clash",
          24: "Rift",
          13: "Rumble",
          23: "Elimination",
          11: "Salvage",
          15: "Doubles",
          28: "Zone Control",
          29: "SRL",
          9: "Skirmish" } 

    mode = 0
    for mode_num, mode_desc in modes.items():
        if args.list_modes:
            print mode_desc
        if mode_desc == args.mode:
            mode = mode_num

    if args.list_modes:
        sys.exit(0)

    with open(args.config_file, 'r') as f:
        config = yaml.load(f)
        f.close()

    lcd = LCD.Adafruit_CharLCDPlate()
    lcd.set_backlight(1)

    psn = args.psn[0]
    headers = { 'X-API-key': config['api_key'] }
    bungie = requests.get("http://www.bungie.net/Platform/Destiny/SearchDestinyPlayer/2/" + psn, headers=headers)
    membership_id = bungie.json()['Response'][0]['membershipId']
    
    last_elo = 0.00
    last_kd  = 0.00

    elo_diff = 0.00
    kd_diff = 0.00

    elo_diff_s = ""
    kd_diff_s = ""

    while True:
	try:
            lcd.clear()
            lcd.message("Updating ...\n")
            time.sleep(3)

            url = "http://api.guardian.gg/fireteam/%i/%s" % (mode, membership_id)
            logging.debug("Getting stats from url: {0}".format(url))
            g_gg = requests.get(url)
            fireteam = g_gg.json()

            for player in fireteam:
                if player['name'] == psn:
                    elo = player['elo']
		    kills = player['kills']
		    deaths = player['deaths']
		    if kills == 0 or deaths == 0:
			kd = 0
		    else:
                    	kd = float(player['kills']) / float(player['deaths'])

                    if last_elo != 0.00 and last_kd != 0.00:
                        if elo != last_elo or kd != last_kd:
                            elo_diff = elo - last_elo
                            kd_diff = kd - last_kd

                            if elo_diff >= 0:
		                elo_diff_s = "+%.3f" % (elo_diff)
		            else:
                                elo_diff_s = str(elo_diff)

                            if kd_diff >= 0:
		                kd_diff_s = "+%.3f" % (kd_diff)
		            else:
                                kd_diff_s = str(kd_diff)

                            lcd.clear()
                            lcd.message("Stats changed!\n")
                            # Blink
                            for i in [0, 1, 0, 1, 0, 1]:
                                lcd.set_backlight(i)
                                time.sleep(1)

                            logging.info("[elo_lcd.py] ELO: %.2f (%s)" % (elo, elo_diff_s))
                            logging.info("[elo_lcd.py] K/D: %.4f (%s)" % (kd, kd_diff_s))
                            
                    lcd.clear()
                    lcd.message("ELO: %i %s\nK/D: %.2f %s" % (elo, elo_diff_s, kd, kd_diff_s))

            last_elo = elo
            last_kd = kd

            # Wait to update again
            time.sleep(300)

        except KeyboardInterrupt:
            lcd.clear()
            lcd.set_backlight(0)
            sys.exit(0)

    # End
    logging.info("[elo_lcd.py] Shutting down ...")

if __name__ == '__main__':
    main()

