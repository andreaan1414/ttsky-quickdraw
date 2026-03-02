import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles


async def reset_dut(dut):
    dut.rst_n.value  = 0
    dut.ui_in.value  = 0
    dut.uio_in.value = 0
    dut.ena.value    = 1
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value  = 1
    await ClockCycles(dut.clk, 2)


async def press_go(dut):
    dut.ui_in.value = dut.ui_in.value | 0x04
    await ClockCycles(dut.clk, 3)


async def wait_for_green_off(dut, max_cycles=8000):
    for _ in range(max_cycles):
        await RisingEdge(dut.clk)
        if (int(dut.uio_out.value) & 0x01) == 0:
            return True
    return False


@cocotb.test()
async def test_reset(dut):
    """After reset: green light off, game over flags off."""
    cocotb.start_soon(Clock(dut.clk, 20, units="ns").start())
    await reset_dut(dut)
    await ClockCycles(dut.clk, 5)
    assert (int(dut.uio_out.value) & 0x01) == 0, "Green should be off after reset"
    assert (int(dut.uio_out.value) & 0x60) == 0, "Game-over flags should be clear"
    dut._log.info("PASS: reset")


@cocotb.test()
async def test_go_starts_green(dut):
    """GO switch turns on the green light."""
    cocotb.start_soon(Clock(dut.clk, 20, units="ns").start())
    await reset_dut(dut)
    await press_go(dut)
    await ClockCycles(dut.clk, 10)
    assert (int(dut.uio_out.value) & 0x01) == 1, "Green should be ON after GO"
    dut._log.info("PASS: GO starts green light")


@cocotb.test()
async def test_player_a_wins_round(dut):
    """Player A flips switch first after green off -> A wins round (uio[1])."""
    cocotb.start_soon(Clock(dut.clk, 20, units="ns").start())
    await reset_dut(dut)
    await press_go(dut)
    assert await wait_for_green_off(dut), "Green never turned off"
    await ClockCycles(dut.clk, 2)
    dut.ui_in.value = 0x01   # Player A
    await ClockCycles(dut.clk, 3)
    assert (int(dut.uio_out.value) >> 1) & 1, "A should win (uio[1])"
    dut._log.info("PASS: Player A wins round")
    dut.ui_in.value = 0x00


@cocotb.test()
async def test_player_b_wins_round(dut):
    """Player B flips switch first after green off -> B wins round (uio[2])."""
    cocotb.start_soon(Clock(dut.clk, 20, units="ns").start())
    await reset_dut(dut)
    await press_go(dut)
    assert await wait_for_green_off(dut), "Green never turned off"
    await ClockCycles(dut.clk, 2)
    dut.ui_in.value = 0x02   # Player B
    await ClockCycles(dut.clk, 3)
    assert (int(dut.uio_out.value) >> 2) & 1, "B should win (uio[2])"
    dut._log.info("PASS: Player B wins round")
    dut.ui_in.value = 0x00


@cocotb.test()
async def test_both_win_after_light(dut):
    """Cheat after light -> both win (uio[3])."""
    cocotb.start_soon(Clock(dut.clk, 20, units="ns").start())
    await reset_dut(dut)
    await press_go(dut)
    assert await wait_for_green_off(dut), "Green never turned off"
    await ClockCycles(dut.clk, 2)
    dut.ui_in.value = 0x08   # cheat
    await ClockCycles(dut.clk, 3)
    assert (int(dut.uio_out.value) >> 3) & 1, "Both should win (uio[3])"
    dut._log.info("PASS: Both win")
    dut.ui_in.value = 0x00


@cocotb.test()
async def test_both_lose_early(dut):
    """Cheat before light -> both lose (uio[4])."""
    cocotb.start_soon(Clock(dut.clk, 20, units="ns").start())
    await reset_dut(dut)
    await press_go(dut)
    await ClockCycles(dut.clk, 5)
    assert (int(dut.uio_out.value) & 0x01) == 1, "Green should still be on"
    dut.ui_in.value = 0x08   # cheat early
    await ClockCycles(dut.clk, 3)
    assert (int(dut.uio_out.value) >> 4) & 1, "Both should lose (uio[4])"
    dut._log.info("PASS: Both lose early")
    dut.ui_in.value = 0x00


@cocotb.test()
async def test_game_over_after_3_wins(dut):
    """Player A winning 3 rounds sets game-over flag (uio[5])."""
    cocotb.start_soon(Clock(dut.clk, 20, units="ns").start())
    await reset_dut(dut)

    for round_num in range(3):
        dut.ui_in.value = 0x04  # GO on
        await ClockCycles(dut.clk, 3)
        assert await wait_for_green_off(dut), f"Green never turned off in round {round_num}"
        await ClockCycles(dut.clk, 2)
        dut.ui_in.value = 0x01  # Player A wins
        await ClockCycles(dut.clk, 3)
        dut.ui_in.value = 0x00  # release all
        await ClockCycles(dut.clk, 5)

    assert (int(dut.uio_out.value) >> 5) & 1, "A game-over flag (uio[5]) should be set"
    dut._log.info("PASS: Game over after 3 A wins")
