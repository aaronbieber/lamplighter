# Lamplighter #

> A lamplighter, historically, was an employee of a town who lit street lights.

This shoddily written Python script will continuously scan the network looking
for certain MAC addresses (perhaps your cell phones). When all MAC addresses are
seen to be missing, the "state" is changed to "away" and Philips Hue lights are
turned off. Upon the return of any MAC address, lights are turned back on.

This labor-saving device is provided as-is, with no representations of fitness
for any purpose, warranty, or licensing requirements whatsoever. It is unlikely
that this script is even useful to anyone else because of its reliance on
specific services, but I provide it here anyway, since someone might learn
something from it.
