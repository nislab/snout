import datetime
import os
import platform
import subprocess
import sys

import click

from pprint import pprint

import scapy.modules.gnuradio as gnuradio
import snout.util as util
import yaml
from prettytable import PrettyTable
from scapy.config import conf as scapy_config
from scapy.themes import DefaultTheme
from snout import Snout
from snout.core.radio import Radio, ScanSelector, TransmitSelector
from snout.core.config import Config as cfg
from snout.util.iot_click import (ProtocolArg, ChannelsOption, PythonLiteralOption,
                                  iot_click, pos_callback, form_cli)

scapy_config.color_theme = DefaultTheme()
scapy_config.dot15d4_protocol = 'zigbee'  # set to zigbee instead of sixlowpan

process = None

# update gnuradio custom modulations
gnuradio.update_custom_modulation(
    protocol='Btle', hardware='hackrf', mode='rx', mode_path='btle_rx')

# Click command line args
######################################################
CONTEXT_SETTINGS = dict(
    help_option_names=["-h", "--help"], max_content_width=110)

# Was using this to invoke help for the latest command
# even when the protocal argument is parsed...changed
# protocol to an option for now though

@click.group(invoke_without_command=False, context_settings=CONTEXT_SETTINGS)
@click.option("automatic", "-auto", "--automatic", cls=PythonLiteralOption,
              help="List of commands to automatically enter. The program generates this")
@click.option("interactive", "-i", "--interactive", is_flag=True,
              help="Interactive guide mode.")
@click.option("display", "-d", "--display", is_flag=True, default=None,
              help="Display the results interactively in the terminal after the scan")
@click.option("hardware", "-h", "--hardware", default=None,
              help="Choose a specific hardware to use. This is useful if several SDRs are plugged in ")
@click.option("filename", "-f", "--filename", default=None,
              help="Filename to dump the ouptut to. If not given, a timestamped file in {} is created".format(cfg.OUTPUTS_DIR))
@click.option("wireshark", "-w", "--wireshark", is_flag=True, default=None,
              help="Open up the test in wireshark")
# ARGUMENTS
@click.argument("protocol", nargs=1, cls=ProtocolArg, required=True,
                type=click.Choice(scapy_config.gr_modulations.keys(), case_sensitive=False))
######################################################
@click.pass_context
def main(
    ctx=None,
    automatic=None,
    interactive=None,
    display=None,
    hardware=None,
    filename=None,
    protocol=None,
    wireshark=None,
):
    """Welcome to Snout!

        This application is designed to provide a powerful and accessible scanning tool for IoT devices with the use of
        Software Defined Radios.
    """
    #pprint(ctx.__dict__)
    #sys.exit()
    app = Snout(
        hardware=hardware,
        protocol=protocol,
        subcommand=ctx.invoked_subcommand,
        automatic=automatic,
        filename=filename,
        wireshark=wireshark,
        display=display
    )
    print("\nWelcome to Snout!")
    if automatic:
        iot_click.set_automatic(automatic)
    if interactive:
        while not app.reqs_satisfied():
            res = None
            robj, rclass, req = app.missing_reqs().pop(0)
            print(rclass, req)
            if rclass=='Snout':
                if req=='protocol':
                    res = iot_click.prompt("\nChoose a protocol",
                        type=click.Choice(list(scapy_config.gr_modulations.keys()) + ['quit'], case_sensitive=False))
                elif req=='subcommand':
                    print(app.subcommand)
                    res = iot_click.prompt("\nChoose a command",
                        type=click.Choice(['scan', 'transmit', 'quit'], case_sensitive=False))
                    ctx.invoked_subcommand = res
            elif rclass=='SDRController':
                if req=='channels':
                    res = get_channels(app.protocol, None)
            if res=='quit':
                sys.exit(-1)
            setattr(robj, req, res)


#    if app.protocol not in app.radio.protocols:
#            valid_hardwares = list(scapy_config.gr_modulations[app.protocol].keys())
#            print('\nProtocol only valid for the following hardwares: {}'.format(
#                ', '.join(valid_hardwares)))
#            print('Searching for compatible hardware...')
#            overlapped_hardwares = [
#                h for h in gnuradio.find_all_hardware(env=app.env) if h in valid_hardwares]
#            if not overlapped_hardwares:
#                print('Could not find compatible hardware')
#                protocol = None
#            else:
#                # Take the highest priority one
#                print('\nFound compatible hardware: {}'.format(
#                    overlapped_hardwares[0]))
#                # already detected
#                radio = Radio(
#                    hardware=overlapped_hardwares[0],
#                    detect=False,
#                    env=app.env
#            )
#    else:
    # Add the args to the context object
    ctx.ensure_object(dict)
    ctx.obj['app'] = app
    ctx.obj['display'] = display
    ctx.obj['filename'] = filename
    ctx.obj['wireshark'] = wireshark


def get_channels(protocol, channels):
    """Gets a range of channels to scan

        Arguments:
                protocol {string} -- the wireless protocol that will be scanned
                all {bool} -- whether or not to return all of the channels for the protocol

        Returns:
                A list of channels
    """
    channel_low, channel_high, channel_default = util.default_channels.get(
        protocol, 
        (None, None, None)
    )
    if protocol == "zwave": # zwave is a special case
        return util.zwave.get_zwave_channels(channels, channel_low, channel_high, channel_default)
    elif channels and channels != 'all':  # if all, just use the low and high bounds
        try:
            assert channels[0] >= channel_low and channels[-1] <= channel_high
        except:
            print('\nChannels for the {} protocol must be in the range of [{}, {}]'.format(
                protocol,
                channel_low,
                channel_high)
            )
            sys.exit(1)
        if isinstance(channels, list):  # do not have to create a range
            return channels
        channel_low = channels[0]  # is a tuple in the form of (low, high)
        channel_high = channels[1]
    elif channels is None:
        channel_low = click.prompt(
            "Enter low channel",
            type=click.IntRange(channel_low, channel_high),
            default=channel_default
        )
        if channel_low != channel_high:
            channel_high = click.prompt(
                "Enter high channel (same as start channel if that is all you want to scan)",
                type=click.IntRange(channel_low, channel_high),
                default=channel_low,
            )
    # create the list of channels according to the low and high channels specified
    return list(range(channel_low, channel_high + 1))


def get_timeout(protocol):
    """Prompts the user for the timeout of the scan

        Arguments:
                protocol {string} -- the wireless protocol that will be scanned
    """
    decode_timeout = -1
    while decode_timeout < 0:
        decode_timeout = click.prompt(
            "Decode Timeout (positive int)",
            type=click.INT,
            default=util.default_timeouts.get(protocol, 10),
        )
    return decode_timeout


def get_packet_threshold():
    """Gets the packet threshold from the user through prompts. Defaults
    to 0 (unlimited packets)
    """
    num_packets = -1
    while num_packets < 0:
        num_packets = click.prompt(
            'Packet Threshold (leave empty to disable)',
            type=click.INT,
            default=0.1,
            show_default=False,
        )
    if num_packets == 0.1:
        return None
    if num_packets < 0:
        raise click.BadOptionUsage('num', '--num INT : int must be >= 0')
    return num_packets


@main.command('scan', short_help='Perform a scan operation')
@click.option("channels", "-c", "--channels", cls=ChannelsOption, default=None,
              help="Specify the channels. Int (11), inclusive range (11:26), list ([11,12,13]), or all (all)")
# Packet Restriction Threshold for each channel
@click.option(
    "active", "-a", "--active", is_flag=True, default=None,
    help="Active Scan"
)
@click.option(
    "packet_threshold", "-n", "--num", type=int, default=None,
    help="Number of packets to scan for each channel"
)
# Timeout for each channel
@click.option(
    "timeout", "-t", "--timeout", type=float,
    help="Add a timeout restriction (in seconds) for each channel.",
)
@click.pass_context
def scan(ctx, active=None, packet_threshold=None, timeout=None, channels=None):
    """Perform a scan operation
    """
    try:
        assert gnuradio.has_scan(ctx.obj['app'].protocol)
    except:
        raise AssertionError(
            'Protocol "{}" does not have a scan option (could not find an rx mode)'.format(ctx.obj['app'].protocol))
    if packet_threshold and packet_threshold < 0:
        raise click.BadOptionUsage('num', '--num INT : int must be >= 0')
    if packet_threshold is None and timeout is None:  # need at least 1 stop condition
        packet_threshold = get_packet_threshold()
        timeout = get_timeout(ctx.obj['app'].protocol)
    if channels == 'all':
        ctx.obj['all'] = True
    # set the args from the scan command
    ctx.obj['scan'] = {}
    ctx.obj['scan']['channels'] = get_channels(ctx.obj['app'].protocol, channels)
    ctx.obj['scan']['num'] = packet_threshold
    ctx.obj['scan']['timeout'] = timeout
    ctx.obj['scan']['active'] = active
    process = ScanSelector.select(ctx.obj['app'].protocol, ctx.obj)
    process.run()
    form_cli(ctx.obj)


@main.command('transmit', short_help='Perform a transmission operation')
@click.option("channels", "-c", "--channels", cls=ChannelsOption, default=None,
              help="Specify the channels. Int (11), inclusive range (11:26), list ([11,12,13]), or all (all)")
@click.pass_context
def transmit(ctx, channels=None):
    """Perform a transmission operation
        \b
        More options are available via prompts after running. Transmits can still
        be run automatically using the outputed command with the --automatic argument
        attached at the end of the transmit, but to form this output you need to
        invoke the prompts at least once.
    """
    try:
        assert gnuradio.has_transmit(ctx.obj['app'].protocol)
    except:
        print('\nProtocol "{}" does not have a transmit option (could not find an rf / tx mode)'.format(
            ctx.obj['app'].protocol)
        )
        sys.exit(1)
    if channels == 'all':
        ctx.obj['all'] = True
    # set the args from the transmit command
    ctx.obj['transmit'] = {}
    ctx.obj['transmit']['channels'] = get_channels(ctx.obj['app'].protocol, channels)
    process = TransmitSelector.select(ctx.obj['app'].protocol, ctx.obj)
    process.run()
    form_cli(ctx.obj)


if __name__ == "__main__":
    try:
        try:
            main()
        except click.Abort:  # click equivalent of a keyboard interrupt
            print("\nQuitting...")
            sys.exit(-1)
    except AttributeError:  # if keyboard interrupt after starting, click will use a string with make_context, which will raise an AttributeError
        sys.exit(0)
