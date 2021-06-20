import sqlite3
import math

conn = sqlite3.connect('data.db')
c = conn.cursor()

calc = True



def add_level(placement, name, creator):
    c.execute('SELECT placement FROM demons ORDER BY placement DESC')
    try:
        lowest_placement = int(c.fetchone()[0])
    except:
        lowest_placement = 0
    if (lowest_placement + 1) >= placement and placement > 0:
        with conn:
            # moves other levels down
            c.execute(f'''UPDATE demons
                        SET placement = placement + 1 
                        WHERE placement >= {placement}''')

            c.execute(f'''INSERT INTO demons (placement, name, creator)
                          VALUES ({placement}, "{name}", "{creator}")''')

        print(f'{name} by {creator} successfully added!')

    else:
        print('\nInvalid placement! Please place levels in a valid range.')



def remove_level(levelname, creator):
    c.execute(f'''SELECT demonid FROM demons
                  WHERE name = "{levelname}"''')
    demon_id = c.fetchone()[0]
    c.execute(f'''SELECT playerid FROM records
                  WHERE demonid = {demon_id}''')
    players = c.fetchall()
    records_removed = 0
    # deletes levels
    with conn:
        c.execute(f'''UPDATE demons
                      SET placement = placement - 1 
                      WHERE placement > (SELECT placement FROM demons
                      WHERE name = "{levelname}" AND creator = "{creator}")''')

        c.execute(f'DELETE FROM demons WHERE name = "{levelname}" AND creator = "{creator}"')
        for i in players:
            c.execute(f'DELETE FROM records WHERE playerid = {i[0]} AND demonid = {demon_id}')
            records_removed += 1
    print(f'\n{levelname} by {creator} deleted successfully!\n{records_removed} records removed.')

def move_level(name, newplace):

    c.execute(f'''SELECT placement FROM demons 
                  WHERE name = "{name}"''')
    
    place = c.fetchone()[0]

    # func for moving levels down
    if place < newplace:
        with conn:
            c.execute(f'''UPDATE demons
                          SET placement = placement - 1
                          WHERE placement > {place} AND placement <= {newplace}''')

    # func for moving a level up
    elif place >= newplace:
        with conn:
            c.execute(f'''UPDATE demons
                          SET placement = placement + 1
                          WHERE placement < {place} AND placement >= {newplace}''')

    with conn:
        c.execute(f'''UPDATE demons
                      SET placement = {newplace}
                      WHERE name = "{name}"''')
    
    print(f'\n{name} moved successfully!\n')


def add_player(name):
    with conn:
        c.execute(f'''INSERT INTO players (name)
                    VALUES ("{name}")''')
    print(f'\n{name} successfully added!')


def remove_player(name):
    c.execute(f'''SELECT playerid FROM players
                  WHERE name = "{name}"''')
    player_id = c.fetchone()[0]
    c.execute(f'''SELECT demonid FROM records
                  WHERE playerid = {player_id}''')
    demons = c.fetchall()
    # deletes player and records
    with conn:
        for i in demons:
            c.execute(f'DELETE FROM records WHERE demonid = {i[0]} AND playerid = {player_id}')
        c.execute(f'''DELETE FROM players 
                      WHERE name = "{name}"''')
    print(f'\n{name} successfully removed!')


def add_record(player_name, level_name):
    c.execute(f'''SELECT playerid FROM players
                  WHERE name = "{player_name}"''')
    player = c.fetchone()[0]
    c.execute(f'''SELECT demonid FROM demons
                  WHERE name = "{level_name}"''')
    demon = c.fetchone()[0]
    with conn:
        c.execute(f'''INSERT INTO records (demonid, playerid)
                      VALUES ({demon}, {player})''')
    print(f'\n{level_name} added to {player_name} successfully!')


def remove_record(player_name, level_name):
    c.execute(f'''SELECT playerid FROM players
                  WHERE name = "{player_name}"''')
    player = c.fetchone()[0]
    c.execute(f'''SELECT demonid FROM demons
                  WHERE name = "{level_name}"''')
    demon = c.fetchone()[0]
    with conn:
        c.execute(f'''DELETE FROM records
                      WHERE playerid = {player} AND demonid = {demon}''')
    print(f'\n{level_name} removed from {player_name} successfully!')


def calc_pts(placement):
    c.execute('SELECT point_curve, legacy_cutoff FROM options')
    settings = c.fetchone()
    # point algorithm ripped from pointercrate :v
    fx = settings[0] * math.e ** ((1-placement) * math.log(1/30) * (1/(-settings[1] + 1)))
    if placement > settings[1]:
        fx = 0
    return fx

def get_points(player_name):
    c.execute(f'''SELECT playerid FROM players
                  WHERE name = "{player_name}"''')
    player = c.fetchone()[0]
    c.execute(f'''SELECT demonid FROM records
                  WHERE playerid = "{player}"''')
    demon = c.fetchall()
    point_count = 0
    for i in demon:
        # loops through demon info and prints
        c.execute(f'''SELECT placement FROM demons
                      WHERE demonid = {i[0]}''')
        demon_info = c.fetchone()
        try:
            point_count += calc_pts(demon_info[0])
        # sqlite returns None if a value doesn't exist so this catches the addition error and keeps looping
        except TypeError:
            pass
    return point_count


def display_profile(player_name):
    func = True
    while func == True:
        c.execute(f'''SELECT playerid FROM players
                    WHERE name = "{player_name}"''')
        try:
            player = c.fetchone()[0]
        except TypeError:
            print('\nCould not find player in the database. Check for typos and try again (it is case sensitive!)')
            break
        c.execute(f'''SELECT demonid FROM records
                    WHERE playerid = "{player}"''')
        demon = c.fetchall()
        # fetches the IDs of player and demon, then prints out a nice multiline list of all the levels
        # and demon count/point count
        c.execute('SELECT legacy_cutoff FROM options')
        list_cut = c.fetchone()[0]
        print(f"\n{player_name}'s profile\n")
        demon_count = 0
        legacy_count = 0
        for i in demon:
            # loops through demon info and prints
            c.execute(f'''SELECT placement, name, creator FROM demons
                        WHERE demonid = {i[0]}''')
            demon_info = c.fetchone()
            print(f'{demon_info[1]} by {demon_info[2]},')
            if demon_info[0] > list_cut:
                legacy_count += 1
            else:
                demon_count += 1
        print(f'\nDemon count: {demon_count}\n\nLegacy demons: {legacy_count}\n\nPoints: {round(get_points(player_name), 2)}')
        break


def level_records(level_name):
    c.execute(f'''SELECT demonid, placement FROM demons
                  WHERE name = "{level_name}"''')
    demon_info = c.fetchone()
    c.execute(f'''SELECT playerid FROM records
                  WHERE demonid = {demon_info[0]}''')
    players = c.fetchall()
    # get IDs n whatever
    print(f'\n{level_name} records:')
    victor_count = 0
    for i in players:
        # loop through and print all victors
        c.execute(f'''SELECT name FROM players
                      WHERE playerid = {i[0]}''')
        print(f'{c.fetchone()[0]}')
        victor_count += 1
    print(f'\nVictor count: {victor_count}\n\nPoints awarded: {round(calc_pts(demon_info[1]), 2)}')


print('''Welcome to cluckwork's Demon List Calculator!
v1.0.3 ''')
while calc == True:
    option = input('''\n1 - View the demons list
2 - Stats viewer
3 - Edit list
4 - Edit stats viewer
5 - Options
6 - Quit
>''')

# demon list
    if option == '1':
        c1 = True
        while c1 == True:
            choice1 = input("\n1 - View the whole list\n2 - Search a level's records\n3 - Back\n>")
            if choice1 == '1':
                c.execute('''SELECT placement, name, creator FROM demons
                            ORDER BY placement ASC''')
                # prints data into a nice list
                for i in c.fetchall():
                    print(f'\n#{i[0]}: {i[1]} by {i[2]} - {round(calc_pts(i[0]), 2)} pts')


            elif choice1 == '2':
                level_name = input("Enter level name: ")
                try:
                    level_records(level_name)
                except TypeError:
                    print("\nCouldn't find this level in the database! It either doesn't exist or you made a typo. (It is case sensitive!)")

            elif choice1 == '3':
                c1 = False

            else:
                print('\nInvalid input!')

# stats viewer 
    elif option == '2':
        c2 = True
        while c2 == True:
            choice2 = input("\n1 - View the whole stats viewer\n2 - Search a specific player\n3 - Back\n>")


            if choice2 == '1':
                c.execute('''SELECT name FROM players''')
                # parses players table - sort by points too
                rank = 0
                detail_list = []
                # below is extremely lazy fix but it works LOL
                # is responsible for sorting by highest pts
                for i in c.fetchall():
                    detail = f'{i[0]} - |{round(get_points(i[0]), 2)}| pts'
                    detail_list.append(detail)
                detail_list = sorted(detail_list, key=lambda x: float(x.partition('|')[2].partition('|')[0]), reverse=True)
                for i in detail_list:
                    rank += 1
                    print(f'#{rank}: {i}')

            elif choice2 == '2':
                player = input("\nEnter player's name: ")
                display_profile(player)
                    

            elif choice2 == '3':
                c2 = False

            else:
                print('\nInvalid input!')

# edit levels
    elif option == '3':
        c3 = True
        while c3 == True:
            choice3 = input('\n1 - Add a level\n2 - Remove a level\n3 - Move a level\n4 - Back\n>')
            if choice3 == '1':
                level_name = input('Level name: ')
                level_creator = input('Level creator: ')
                try:
                    level_placement = int(input('Level placement: '))
                except ValueError:
                    print("\nInvalid input! Enter a number, don't include a hashtag")
                    break
                confirm = input(f'Are you sure you want to place {level_name} by {level_creator} at #{level_placement}? (Y/N) ')
                if confirm.upper() == 'Y':
                    add_level(level_placement, level_name, level_creator)
                else:
                    pass

            elif choice3 == '2':
                level_name = input('Level name: ')
                c.execute(f'''SELECT placement, creator
                              FROM demons
                              WHERE name = "{level_name}"''')
                level_info = c.fetchone()
                try:
                    confirm = input(f'Are you sure you want to remove {level_name} by {level_info[1]}? (placed at #{level_info[0]}) (Y/N)\n>')
                except TypeError:
                    # Backs out if level placement returned is null
                    print("\nCan't find this level in the database. Check for typos and try again (it is case sensitive!)")
                    break
                if confirm.upper() == 'Y':
                    remove_level(level_name, level_info[1])
                else:
                    pass

            elif choice3 == '3':
                level_name = input('\nWhat level would you like to move?: ')
                new_placement = int(input('\nWhere would you like to move it to? (Just enter a number): '))
                c.execute(f'''SELECT placement, creator
                              FROM demons
                              WHERE name = "{level_name}"''')
                level_info = c.fetchone()
                try:
                    confirm = input(f'Are you sure you want to move {level_name} by {level_info[1]} from #{level_info[0]} to #{new_placement}? (Y/N)\n>')
                    if confirm.upper() == 'Y':
                        move_level(level_name, new_placement)
                except TypeError:
                    # Backs out if level placement returned is null
                    print("\nCan't find this level in the database. Check for typos and try again (it is case sensitive!)")

                

            elif choice3 == '4':
                c3 = False

            else:
                print('\nInvalid input!')

# edit players
    elif option == '4':
        c4 = True
        while c4 == True:
            choice4 = input('\n1 - Add a player\n2 - Remove a player\n3 - Change username\n4 - Add a record\n5 - Remove a record\n6 - Back\n>')
            if choice4 == '1':
                player_name = input("\nEnter player's name: ")
                confirm = input(f'\nAre you sure you want to add {player_name} to the stats viewer? (Y/N)\n>')
                if confirm.upper() == 'Y':
                    add_player(player_name)
                else:
                    pass

            elif choice4 == '2':
                player_name = input("\nEnter the player's name: ")
                confirm = input(f'\nAre you sure you want to remove {player_name} from the stats viewer? (Y/N)\n>')
                if confirm.upper() == 'Y':
                    remove_player(player_name)
                else:
                    pass
            
            elif choice4 == '3':
                player_name = input("\nEnter player's current name: ")
                new_name = input("\nEnter their new name: ")
                confirm = input(f"\nAre you sure you want to change {player_name}'s name to {new_name}? (Y/N)\n>")
                if confirm.upper() == 'Y':
                    with conn:
                        c.execute(f'''UPDATE players
                                      SET name = "{new_name}"
                                      WHERE name = "{player_name}"''')
                    print(f'\n{player_name} changed to {new_name} successfully!')
                else:
                    pass
            
            elif choice4 == '4':
                player_name = input("\nEnter player's name: ")
                level_name = input("\nEnter level name: ")
                c.execute(f'''SELECT placement, creator
                              FROM demons
                              WHERE name = "{level_name}"''')
                level_info = c.fetchone()
                try:
                    confirm = input(f'\nAre you sure you want to add {level_name} by {level_info[1]} (placed at #{level_info[0]}) to {player_name}? (Y/N)\n>')
                except TypeError:
                    # Backs out if level placement returned is null
                    print("\nCan't find the level or player in the database. Check for typos and try again (it is case sensitive!)")
                    break
                if confirm.upper() == 'Y':
                    add_record(player_name, level_name)
                else:
                    pass

            elif choice4 == '5':
                player_name = input("\nEnter player's name: ")
                level_name = input("\nEnter level name: ")
                c.execute(f'''SELECT placement, creator
                              FROM demons
                              WHERE name = "{level_name}"''')
                level_info = c.fetchone()
                try:
                    confirm = input(f'\nAre you sure you want to remove {level_name} by {level_info[1]} (placed at #{level_info[0]}) from {player_name}? (Y/N)\n>')
                except TypeError:
                    # Backs out if level placement returned is null
                    print("\nCan't find this level in the database. Check for typos and try again (it is case sensitive!)")
                    break
                if confirm.upper() == 'Y':
                    remove_record(player_name, level_name)
                else:
                    pass

            elif choice4 == '6':
                c4 = False

            else:
                print('\nInvalid input!')
    #settings 
    elif option == '5':
        o5 = True
        while o5 == True:
            option5 = input('\n1 - Adjust point formula\n2 - Adjust number of list levels\n3 - Delete all data\n4 - Back\n>')
            if option5 == '1':
                peak = input('\nEnter the amount of points you would like the #1 level to give. The rest of the levels will adjust accordingly: ')
                confirm = input(f'\nAre you sure you want to set the point peak to {peak}? (this can be changed later) (Y/N)\n>')
                if confirm.upper() == 'Y':
                    # tries to update the int and returns error if the value isn't valid
                    try:
                        with conn:
                            c.execute(f'''UPDATE options
                                        SET point_curve = {peak}''')
                    except sqlite3.OperationalError:
                        print("\nInvalid input! Enter a number, don't include a hashtag")
                else:
                    pass
            
            elif option5 == '2':
                cutoff = input('\nAt what placement should levels become legacy? (all placements below will be included in the legacy list): ')
                confirm = input(f'\nAre you sure you want to set the last list level to #{cutoff}? (Y/N)\n>')
                if confirm.upper() == 'Y':
                    # tries to update the int and returns error if the value isn't valid
                    try:
                        with conn:
                            c.execute(f'''UPDATE options
                                        SET legacy_cutoff = {cutoff}''')
                    except sqlite3.OperationalError:
                        print("\nInvalid input! Enter a number with no decimal point, don't include a hashtag")
                else:
                    pass
            
            elif option5 == '3':
                confirm = input('\nAre you sure you want to delete all data? This cannot be undone (type CONFIRM to continue, anything else to go back)\n>')
                if confirm.upper() == 'CONFIRM':
                    with conn:
                        c.execute('DELETE FROM demons')
                        c.execute('DELETE FROM players')
                        c.execute('DELETE FROM records')
                        c.execute('''UPDATE options
                                     SET point_curve = 150, legacy_cutoff = 150''')
                    print('\nDeletion successful, legacy cutoff and point peak reset to 150.')
                else:
                    pass


            elif option5 == '4':
                o5 = False

            else:
                print('\nInvalid input!')

    elif option == '6':
        calc = False

    elif option == 'troll':
        print('''░░░░░▄▄▄▄▀▀▀▀▀▀▀▀▄▄▄▄▄▄░░░░░░░
░░░░░█░░░░▒▒▒▒▒▒▒▒▒▒▒▒░░▀▀▄░░░░
░░░░█░░░▒▒▒▒▒▒░░░░░░░░▒▒▒░░█░░░
░░░█░░░░░░▄██▀▄▄░░░░░▄▄▄░░░░█░░
░▄▀▒▄▄▄▒░█▀▀▀▀▄▄█░░░██▄▄█░░░░█░
█░▒█▒▄░▀▄▄▄▀░░░░░░░░█░░░▒▒▒▒▒░█
█░▒█░█▀▄▄░░░░░█▀░░░░▀▄░░▄▀▀▀▄▒█
░█░▀▄░█▄░█▀▄▄░▀░▀▀░▄▄▀░░░░█░░█░
░░█░░░▀▄▀█▄▄░█▀▀▀▄▄▄▄▀▀█▀██░█░░
░░░█░░░░██░░▀█▄▄▄█▄▄█▄████░█░░░
░░░░█░░░░▀▀▄░█░░░█░█▀██████░█░░
░░░░░▀▄░░░░░▀▀▄▄▄█▄█▄█▄█▄▀░░█░░
░░░░░░░▀▄▄░▒▒▒▒░░░░░░░░░░▒░░░█░
░░░░░░░░░░▀▀▄▄░▒▒▒▒▒▒▒▒▒▒░░░░█░
░░░░░░░░░░░░░░▀▄▄▄▄▄░░░░░░░░█░░''')

    else:
        print('\nInvalid input!')

conn.close()
