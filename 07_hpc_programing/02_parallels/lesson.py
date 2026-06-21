import asyncio


async def task(name, seconds):
    print(f"Task {name} started, will take {seconds} seconds.")
    await asyncio.sleep(seconds)
    print(f"Task {name} completed.")

async def main():
    await asyncio.gather(
        task("task1", 10),
        task("task2", 20),
    )


asyncio.run(main())