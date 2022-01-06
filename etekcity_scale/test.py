import asyncio

from bleak import BleakClient

import etekcity_scale.packet as packet

BATTERY_SERVICE = "0000180f-0000-1000-8000-00805f9b34fb"
BATTERY_CHR = "00002A19-0000-1000-8000-00805f9b34fb"
SCALES_SERVICE = "0000fff0-0000-1000-8000-00805f9b34fb"
NOTIFY_CHR = "0000fff1-0000-1000-8000-00805f9b34fb"
CONFIG_CHR = "0000fff2-0000-1000-8000-00805f9b34fb"

send_queue = asyncio.Queue()


def notification_handler(sender, data):

    p = packet.decode_packet(data)

    if isinstance(p, packet.HelloPacket):
        send_queue.put_nowait(packet.init_packet(display_units="KG"))

    elif isinstance(p, packet.UnknownPacket) and p.type == 0x14:
        send_queue.put_nowait(packet.set_time_packet())

    elif isinstance(p, packet.UnknownPacket) and p.type == 0x21:
        send_queue.put_nowait(packet.init2_packet())

    elif isinstance(p, packet.WeightMeasurement):
        print(p.weight_kg, p.final, p.r1, p.r2)

        if p.final:
            send_queue.put_nowait(packet.finish_measurement())

    else:
        print(p)


async def run_scales(client: BleakClient, service):

    await client.start_notify(NOTIFY_CHR, notification_handler)

    while True:
        packet = await send_queue.get()
        if packet is None:
            break
        await client.write_gatt_char(CONFIG_CHR, packet)


def on_disconnected(client):
    send_queue.put_nowait(None)


async def main(args):
    async with BleakClient(args.mac_address) as client:

        client.set_disconnected_callback(on_disconnected)

        services = await client.get_services()

        for s in services:
            if s.uuid == BATTERY_SERVICE:
                print("Battery", await client.read_gatt_char(BATTERY_CHR))
            if s.uuid == SCALES_SERVICE:
                print("Found scales service")
                await run_scales(client, s)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser("Test programme for EtekCity")
    parser.add_argument("mac_address", type=str,
                        help="MAC address of your scales")

    args = parser.parse_args()

asyncio.run(main(args))
