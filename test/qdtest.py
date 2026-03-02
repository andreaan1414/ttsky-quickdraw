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


def green_light(dut):
    """Green light = uio_out[0]"""
    return (int(dut.uio_out.value) & 0x01)


async def start_round(dut):
    """Flip GO switch on, wait a few cycles, flip off"""
    dut.ui_in.value = 0x04   # ui[2] = GO
    await ClockCycles(dut.clk, 3)
    dut.ui_in.value = 0x00
    await ClockCycles(dut.clk, 2)


async def wait_green_off(dut, max_cycles=8000):
    """Wait until green light goes low (timer expired)"""
    for _ in range(max_cycles):
        await RisingEdge(dut.clk)
        if green_light(dut) == 0:
            return True
    return False


# ----------------------------------------------------------------
# Tests - mirroring your Vivado quickDrawSimulation.v scenarios
# ----------------------------------------------------------------

@cocotb.test()
async def test_reset(dut):
    """After reset everything should be idle - green light off"""
    cocotb.start_soon(Clock(dut.clk, 20, units="ns").start())
    await reset_dut(dut)
    await ClockCycles(dut.clk, 5)
    assert green_light(dut) == 0, "Green should be OFF after reset"
    assert (int(dut.uio_out.value) & 0x60) == 0, "Game over flags should be clear"
    dut._log.info("PASS: reset")


@cocotb.test()
async def test_go_turns_green_on(dut):
    """Flipping GO should turn the green light on"""
    cocotb.start_soon(Clock(dut.clk, 20, units="ns").start())
    await reset_dut(dut)
    await start_round(dut)
    await ClockCycles(dut.clk, 5)
    assert green_light(dut) == 1, "Green should be ON after GO"
    dut._log.info("PASS: GO turns green on")


@cocotb.test()
async def test_player_a_wins(dut):
    """Player A flips after green off -> A wins (uio[1] high, 7seg shows A)"""
    cocotb.start_soon(Clock(dut.clk, 20, units="ns").start())
    await reset_dut(dut)
    await start_round(dut)
    assert await wait_green_off(dut), "Green never turned off"
    await ClockCycles(dut.clk, 2)

    dut.ui_in.value = 0x01   # Player A flips
    await ClockCycles(dut.clk, 3)

    assert (int(dut.uio_out.value) >> 1) & 1, "uio[1] A wins should be high"
    dut._log.info("PASS: Player A wins")

    # release switch, return to idle
    dut.ui_in.value = 0x00
    await ClockCycles(dut.clk, 5)


@cocotb.test()
async def test_player_b_wins(dut):
    """Player B flips after green off -> B wins (uio[2] high)"""
    cocotb.start_soon(Clock(dut.clk, 20, units="ns").start())
    await reset_dut(dut)
    await start_round(dut)
    assert await wait_green_off(dut), "Green never turned off"
    await ClockCycles(dut.clk, 2)

    dut.ui_in.value = 0x02   # Player B flips
    await ClockCycles(dut.clk, 3)

    assert (int(dut.uio_out.value) >> 2) & 1, "uio[2] B wins should be high"
    dut._log.info("PASS: Player B wins")

    dut.ui_in.value = 0x00
    await ClockCycles(dut.clk, 5)


@cocotb.test()
async def test_both_win(dut):
    """Both flip at same time after green off -> both win (uio[3] high)"""
    cocotb.start_soon(Clock(dut.clk, 20, units="ns").start())
    await reset_dut(dut)
    await start_round(dut)
    assert await wait_green_off(dut), "Green never turned off"
    await ClockCycles(dut.clk, 2)

    dut.ui_in.value = 0x08   # cheat switch = both fire simultaneously
    await ClockCycles(dut.clk, 3)

    assert (int(dut.uio_out.value) >> 3) & 1, "uio[3] both win should be high"
    dut._log.info("PASS: Both win")

    dut.ui_in.value = 0x00
    await ClockCycles(dut.clk, 5)


@cocotb.test()
async def test_both_lose_early(dut):
    """Both flip BEFORE green off -> both lose (uio[4] high)"""
    cocotb.start_soon(Clock(dut.clk, 20, units="ns").start())
    await reset_dut(dut)
    await start_round(dut)

    # Green should still be on
    await ClockCycles(dut.clk, 5)
    assert green_light(dut) == 1, "Green should still be ON"

    dut.ui_in.value = 0x08   # cheat early
    await ClockCycles(dut.clk, 3)

    assert (int(dut.uio_out.value) >> 4) & 1, "uio[4] both lose should be high"
    dut._log.info("PASS: Both lose early")

    dut.ui_in.value = 0x00
    await ClockCycles(dut.clk, 5)


@cocotb.test()
async def test_early_flip_a_loses(dut):
    """Player A flips early -> B wins (uio[2] high)"""
    cocotb.start_soon(Clock(dut.clk, 20, units="ns").start())
    await reset_dut(dut)
    await start_round(dut)

    await ClockCycles(dut.clk, 5)
    assert green_light(dut) == 1, "Green should still be ON"

    dut.ui_in.value = 0x01   # Player A flips early
    await ClockCycles(dut.clk, 3)

    assert (int(dut.uio_out.value) >> 2) & 1, "uio[2] B wins (A flipped early)"
    dut._log.info("PASS: Early flip A loses, B wins")

    dut.ui_in.value = 0x00
    await ClockCycles(dut.clk, 5)


@cocotb.test()
async def test_game_over_first_to_3(dut):
    """Player A winning 3 rounds triggers game over (uio[5] high)"""
    cocotb.start_soon(Clock(dut.clk, 20, units="ns").start())
    await reset_dut(dut)

    for i in range(3):
        dut.ui_in.value = 0x04  # GO
        await ClockCycles(dut.clk, 3)
        dut.ui_in.value = 0x00
        assert await wait_green_off(dut), f"Green never off in round {i}"
        await ClockCycles(dut.clk, 2)
        dut.ui_in.value = 0x01  # A wins
        await ClockCycles(dut.clk, 3)
        dut.ui_in.value = 0x00
        await ClockCycles(dut.clk, 5)

    assert (int(dut.uio_out.value) >> 5) & 1, "uio[5] game over A should be set"
    dut._log.info("PASS: Game over after 3 A wins")
