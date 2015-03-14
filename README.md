# Lamplighter #

> A lamplighter, historically, was an employee of a town who lit street lights.

Lamplighter is a presence management tool that might fit into your home
automation suite; it monitors the network for a list of MAC addresses and
acts as a state machine tracking whether the listed devices are present. When
the state changes (from "home" to "away" or vice-versa), user-defined callbacks
are triggered, which can do anything you need them to.

Lamplighter's name is inspired by its original use case: to turn the lights off
when the house is empty, and to turn them back on upon anyone's return.

Lamplighter also understands the concept of "quiet hours," which is simply a
range of time during which your callback functions can do something different.
For example, you may want to set a period of time during the night where
Lamplighter will never turn the lights on or off but instead write to a log file
or send you a text message.

Lamplighter uses the `nmap` and `arp-scan` utilities to look for MAC addresses
on the network. Typically, wireless devices are the right choice for this scan,
otherwise it would be rather pointless, and scanning for wireless devices is
error-prone. Two utilities are used to reduce false negatives, and the quiet
hours feature exists to protect against unwanted home automation activities
taking place while you're trying to sleep.

This labor-saving device is provided as-is, with no representations of fitness
for any purpose, warranty, or licensing requirements whatsoever. It is unlikely
that this script is even useful to anyone else because of its reliance on
specific services, but I provide it here anyway, since someone might learn
something from it.

## Setup ##

It's easy to get Lamplighter running. Simply:

  1. Make sure you have `nmap` and `arp-scan` installed.
  2. Configure `sudoers` so that `nmap` and `arp-scan` can both be run with
     escalated privileges (because promiscuous network scanning requires
     it). How this is accomplished depends on how Lamplighter itself is run; if
     Lamplighter is run as root, there is no need to configure `sudoers` at
     all. If Lamplighter runs as a user account, that user account should be set
     up to allow `sudo nmap` and `sudo arp-scan` to be run without a password.
  3. Rename `config_example.ini` to `config.ini` and enter appropriate values.
  4. Rename `dispatcher_example.py` to `dispatcher.py` (or any other name of
     your choosing) and write useful callback functions that do whatever you
     want them to, following the pattern in the example.
  5. Run your dispatcher script, preferably using a daemon management system
     like Supervisor or Upstart.
