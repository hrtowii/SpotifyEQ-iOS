import traceback
from pathlib import Path
import click
from packaging.version import parse as parse_version
from pymobiledevice3.cli.cli_common import Command
from pymobiledevice3.exceptions import NoDeviceConnectedError, PyMobileDevice3Exception
from pymobiledevice3.lockdown import LockdownClient, create_using_usbmux, create_using_tcp
from pymobiledevice3.services.installation_proxy import InstallationProxyService
from sparserestore import backup, perform_restore
import shutil
import plistlib
global lockdown
lockdown = create_using_usbmux(autopair=True)
def exit(code=0):
    return code

def apply_eq(service_provider: LockdownClient) -> None:
    if Path('./modded-equalizer-presets.plist').exists() == False:
        print("Edit your EQ preset first!")
        return
    device_class = service_provider.get_value(key="DeviceClass")
    device_build = service_provider.get_value(key="BuildVersion")
    device_version = parse_version(service_provider.product_version)

    if not all([device_class, device_build, device_version]):
        click.secho("Failed to get device information!", fg="red")
        click.secho("Make sure your device is connected and try again.", fg="red")
        return
    
    app = "Spotify.app"

    apps_json = InstallationProxyService(service_provider).get_apps(application_type="User", calculate_sizes=False)

    app_path = None
    for key, value in apps_json.items():
        if isinstance(value, dict) and "Path" in value:
            potential_path = Path(value["Path"])
            if potential_path.name.lower() == app.lower():
                app_path = potential_path
                app = app_path.name
                print(app_path)

    app_uuid = app_path.parent.name

    try:
        with open('./modded-equalizer-presets.plist', "rb") as helper_contents:
            click.secho(f"Replacing {app}/equalizer-presets (UUID: {app_uuid})", fg="yellow")
            back = backup.Backup(
                files=[
                    backup.ConcreteFile(
                        "",
                        f"SysContainerDomain-../../../../../../../../var/containers/Bundle/Application/{app_uuid}/{app}/equalizer-presets.plist",
                        owner=33,
                        group=33,
                        contents=helper_contents.read(),
                    ),
                    backup.ConcreteFile("", "SysContainerDomain-../../../../../../../.." + "/crash_on_purpose", contents=b""),
                ]
            )
    except Exception as e:
        click.secho(f"ERROR: {e}", fg="red")
        return
    try:
        perform_restore(back, reboot=False)
    except PyMobileDevice3Exception as e:
        if "Find My" in str(e):
            click.secho("Find My must be disabled in order to use this tool.", fg="red")
            click.secho("Disable Find My from Settings (Settings -> [Your Name] -> Find My) and then try again.", fg="red")
            exit(1)
        elif "crash_on_purpose" not in str(e):
            raise e

    click.secho("Make sure you turn Find My iPhone back on if you use it after rebooting.", fg="green")

def reset_eq(service_provider: LockdownClient) -> None:
    device_class = service_provider.get_value(key="DeviceClass")
    device_build = service_provider.get_value(key="BuildVersion")
    device_version = parse_version(service_provider.product_version)

    if not all([device_class, device_build, device_version]):
        click.secho("Failed to get device information!", fg="red")
        click.secho("Make sure your device is connected and try again.", fg="red")
        return

    app = "Spotify.app"

    apps_json = InstallationProxyService(service_provider).get_apps(application_type="User", calculate_sizes=False)

    app_path = None
    for key, value in apps_json.items():
        if isinstance(value, dict) and "Path" in value:
            potential_path = Path(value["Path"])
            if potential_path.name.lower() == app.lower():
                app_path = potential_path
                app = app_path.name
                print(app_path)

    app_uuid = app_path.parent.name

    try:
        with open('./original-equalizer-presets.plist', "rb") as helper_contents: # TODO: use relative paths for this. but basically the swift app should add the assets file here
            click.secho(f"Replacing {app} (UUID: {app_uuid})", fg="yellow")
            back = backup.Backup(
                files=[
                    backup.ConcreteFile(
                        "",
                        f"SysContainerDomain-../../../../../../../../var/containers/Bundle/Application/{app_uuid}/{app}/equalizer-presets.plist",
                        owner=33,
                        group=33,
                        contents=helper_contents.read(),
                    ),
                    backup.ConcreteFile("", "SysContainerDomain-../../../../../../../.." + "/crash_on_purpose", contents=b""),
                ]
            )
    except Exception as e:
        click.secho(f"ERROR: {e}", fg="red")
        return
    try:
        perform_restore(back, reboot=False)
    except PyMobileDevice3Exception as e:
        if "Find My" in str(e):
            click.secho("Find My must be disabled in order to use this tool.", fg="red")
            click.secho("Disable Find My from Settings (Settings -> [Your Name] -> Find My) and then try again.", fg="red")
            exit(1)
        elif "crash_on_purpose" not in str(e):
            raise e

    click.secho("Make sure you turn Find My iPhone back on if you use it after rebooting.", fg="green")

def menu():
    print("\033[1;32mSpotifyEQ-iOS\033[0;m")
    print("by htrowii / sacrosanctuary")
    print("v1.0")
    print("Back up your device first!")
    exited = False
    while exited is False:
        print("1. Add equalizer preset")
        print("2. Reset equalizer presets")
        print("3. Apply equalizer presets")
        print("4. Exit")
        try:
            option = int(input("Enter option: "))
        except ValueError:
            print("Type in a number!")
            menu()
        if option == 1:
            create_modded_eq()
        elif option == 2:
            reset_eq(lockdown)
        elif option == 3:
            apply_eq(lockdown)
        elif option == 4:
            exited = True
            exit(0)

# todo: import CSV
# todo: use autoeq preset -> later?
# basic usage:
# while true, ask for band freq, then the decibel
# after that, do the math by normalising db by within +/-12db range
def create_modded_eq():
    exitmodding = False
    if Path('./modded-equalizer-presets.plist').exists() == False:
        print("Creating duplicate to edit...")
        shutil.copyfile('./original-equalizer-presets.plist', './modded-equalizer-presets.plist')
    while exitmodding is False:
        print("1. Add bands")
        print("2. Import csv file - \033[1;31mUNFINISHED\033[0;m")
        print("3. Get autoEQ preset - \033[1;31mUNFINISHED\033[0;m")
        print("4. Exit to main menu")
        try:
            mod_option = int(input("Enter option: "))
        except ValueError:
            print("Type in a number!")
            create_modded_eq()
        if mod_option == 1:
            add_bands()
        elif mod_option == 4:
            exitmodding = True
        else:
            print("Unfinished!")

def return_frequency_gain():
    try:
        frequency = float(input("Enter frequency in hertz: "))
        gain = float(input("Enter gain in db: "))
        return frequency, gain
    except ValueError:
        print("Type in a number!")
        return return_frequency_gain()

def add_bands():
    presets = []
    bands_no = int(input("How many frequency bands? \033[1;33mNote that Q factor can't be changed\033[0;m: "))
    count = 0
    with open('modded-equalizer-presets.plist', 'rb') as plistbytes:
        plist = plistlib.loads(plistbytes.read())
        # print(plist)
        for preset in plist['presets']:
            presets.append(preset['name'].lower())
        print(f"Presets: {presets}")
        valid_preset = False
        while valid_preset is False:
            preset_to_overwrite = input("Choose which preset you want to overwrite: ")
            if preset_to_overwrite.lower() not in presets:
                print("Enter a valid preset!")
            else:
                valid_preset = True
        # null out the preset bands
        for preset in plist['presets']:
            if preset['name'].lower() == preset_to_overwrite.lower():
                preset['values'] = []
                while count < bands_no:
                    frequency, gain = return_frequency_gain()
                    # normalise gain. -1 to 1 is -12db to 12db so do the math
                    normalized_gain = gain / 12
                    preset['values'].append({'frequency': frequency, 'value': normalized_gain})
                    # take the modded-presets.plist and open it into a readable format
                    count += 1
                # break
        # writeback
    with open('modded-equalizer-presets.plist', 'wb') as plistbytes:
        plistlib.dump(plist, plistbytes)
        print("Edited plist! Apply it in the previous menu. ")

def main():
    try:
        menu()
    except NoDeviceConnectedError:
        click.secho("No device connected!", fg="red")
        click.secho("Please connect your device and try again.", fg="red")
        exit(1)
    except click.UsageError as e:
        click.secho(e.format_message(), fg="red")
        exit(2)
    except Exception:
        click.secho("An error occurred!", fg="red")
        click.secho(traceback.format_exc(), fg="red")
        exit(1)

if __name__ == "__main__":
    main()
