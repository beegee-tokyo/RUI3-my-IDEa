/**
 * @file RAK1904_acc.cpp
 * @author Bernd Giesecke (bernd@giesecke.tk)
 * @brief Initialize and read values from the LIS3DH sensor
 * @version 0.1
 * @date 2022-04-11
 *
 * @copyright Copyright (c) 2022
 *
 */
#include "main.h"
#include <Adafruit_LIS3DH.h>
#include <Adafruit_Sensor.h>

//******************************************************************//
// RAK1904 INT1_PIN
//******************************************************************//
// Slot A      WB_IO1
// Slot B      WB_IO2 ( not recommended, pin conflict with IO2)
// Slot C      WB_IO3
// Slot D      WB_IO5
// Slot E      WB_IO4
// Slot F      WB_IO6
//******************************************************************//

/** Interrupt pin, depends on slot */
#if __has_include("RAK1904_acc_S_A.h")
#include "RAK1904_acc_S_A.h"
#elif __has_include("RAK1904_acc_S_B.h")
#include "RAK1904_acc_S_B.h"
#elif __has_include("RAK1904_acc_S_C.h")
#include "RAK1904_acc_S_C.h"
#elif __has_include("RAK1904_acc_S_D.h")
#include "RAK1904_acc_S_D.h"
#elif __has_include("RAK1904_acc_S_E.h")
#include "RAK1904_acc_S_E.h"
#elif __has_include("RAK1904_acc_S_F.h")
#include "RAK1904_acc_S_F.h"
#elif
uint8_t acc_int_pin = WB_IO3;
#endif

// Forward declarations
void int_callback_rak1904(void);

/** Sensor instance using Wire */
Adafruit_LIS3DH acc_sensor(&Wire);

/** For internal usage */
TwoWire *usedWire;

/** Last time a motion was detected */
time_t last_trigger = 0;

/** Flag if motion was detected */
bool motion_detected = false;

/**
 * @brief Read RAK1904 register
 *     Added here because Adafruit made that function private :-(
 *
 * @param chip_reg register address
 * @param dataToWrite data to write
 * @return true write success
 * @return false write failed
 */
bool rak1904_writeRegister(uint8_t chip_reg, uint8_t dataToWrite)
{
	// Write the byte
	usedWire->beginTransmission(LIS3DH_DEFAULT_ADDRESS);
	usedWire->write(chip_reg);
	usedWire->write(dataToWrite);
	if (usedWire->endTransmission() != 0)
	{
		return false;
	}

	return true;
}

/**
 * @brief Write RAK1904 register
 *     Added here because Adafruit made that function private :-(
 *
 * @param outputPointer
 * @param chip_reg
 * @return true read success
 * @return false read failed
 */
bool rak1904_readRegister(uint8_t *outputPointer, uint8_t chip_reg)
{
	// Return value
	uint8_t result;
	uint8_t numBytes = 1;

	usedWire->beginTransmission(LIS3DH_DEFAULT_ADDRESS);
	usedWire->write(chip_reg);
	if (usedWire->endTransmission() != 0)
	{
		return false;
	}
	usedWire->requestFrom(LIS3DH_DEFAULT_ADDRESS, numBytes);
	while (usedWire->available()) // slave may send less than requested
	{
		result = usedWire->read(); // receive a byte as a proper uint8_t
	}

	*outputPointer = result;
	return true;
}

/**
 * @brief Initialize LIS3DH 3-axis
 * acceleration sensor
 *
 * @return true If sensor was found and is initialized
 * @return false If sensor initialization failed
 */
bool init_rak1904(void)
{
	// Setup interrupt pin
	pinMode(acc_int_pin, INPUT);

	Wire.begin();
	usedWire = &Wire;

	acc_sensor.setDataRate(LIS3DH_DATARATE_10_HZ);
	acc_sensor.setRange(LIS3DH_RANGE_4_G);

	if (!acc_sensor.begin())
	{
		MYLOG("ACC", "ACC sensor initialization failed");
		return false;
	}

	// Enable interrupts
	acc_sensor.enableDRDY(true, 1);
	acc_sensor.enableDRDY(false, 2);

	uint8_t data_to_write = 0;
	data_to_write |= 0x20;									  // Z high
	data_to_write |= 0x08;									  // Y high
	data_to_write |= 0x02;									  // X high
	rak1904_writeRegister(LIS3DH_REG_INT1CFG, data_to_write); // Enable interrupts on high tresholds for x, y and z

	// Set interrupt trigger range
	data_to_write = 0;
#ifdef _RAK12500_GNSS_H_
	// Check if Helium Mapper is enabled
	if (gnss_format == 2)
	{
		data_to_write |= 0x3; // A lower threshold for mapping purposes
		MYLOG("ACC", "Set high sensitivity for Helium Mapper");
	}
	else
	{
		data_to_write |= 0x10; // 1/8 range
		MYLOG("ACC", "Set normal sensitivity");
	}
#else  // _RAK12500_GNSS_H_
	data_to_write |= 0x10; // 1/8 range
#endif // _RAK12500_GNSS_H_

	rak1904_writeRegister(LIS3DH_REG_INT1THS, data_to_write); // 1/8th range

	// Set interrupt signal length
	data_to_write = 0;
	data_to_write |= 0x01; // 1 * 1/50 s = 20ms
	rak1904_writeRegister(LIS3DH_REG_INT1DUR, data_to_write);

	rak1904_readRegister(&data_to_write, LIS3DH_REG_CTRL5);
	data_to_write &= 0xF3;									// Clear bits of interest
	data_to_write |= 0x08;									// Latch interrupt (Cleared by reading int1_src)
	rak1904_writeRegister(LIS3DH_REG_CTRL5, data_to_write); // Set interrupt to latching

	// Select interrupt pin 1
	data_to_write = 0;
	data_to_write |= 0x40; // AOI1 event (Generator 1 interrupt on pin 1)
	data_to_write |= 0x20; // AOI2 event ()
	rak1904_writeRegister(LIS3DH_REG_CTRL3, data_to_write);

	// No interrupt on pin 2
	rak1904_writeRegister(LIS3DH_REG_CTRL6, 0x00);

	// Enable high pass filter
	rak1904_writeRegister(LIS3DH_REG_CTRL2, 0x01);

	// Set low power mode
	data_to_write = 0;
	rak1904_readRegister(&data_to_write, LIS3DH_REG_CTRL1);
	data_to_write |= 0x08;
	rak1904_writeRegister(LIS3DH_REG_CTRL1, data_to_write);
	delay(100);
	data_to_write = 0;
	rak1904_readRegister(&data_to_write, 0x1E);
	data_to_write |= 0x90;
	rak1904_writeRegister(0x1E, data_to_write);
	delay(100);

	clear_int_rak1904();

	// Set the interrupt callback function
	MYLOG("ACC", "Int pin %s", acc_int_pin == WB_IO3 ? "WB_IO3" : "WB_IO5");
	attachInterrupt(acc_int_pin, int_callback_rak1904, RISING);

	last_trigger = millis();

	return true;
}

/**
 * @brief Reads the values from the LIS3DH sensor
 *
 */
void read_rak1904(void)
{
	sensors_event_t event;
	acc_sensor.getEvent(&event);
	MYLOG("ACC", "Acceleration in g (x,y,z): %f %f %f", event.acceleration.x, event.acceleration.y, event.acceleration.z);
}

/**
 * @brief Assign/reassing interrupt pin
 *
 * @param new_irq_pin new GPIO to assign to interrupt
 */
void int_assign_rak1904(uint8_t new_irq_pin)
{
	detachInterrupt(acc_int_pin);
	acc_int_pin = new_irq_pin;
	attachInterrupt(acc_int_pin, int_callback_rak1904, RISING);
}

/**
 * @brief ACC interrupt handler
 * @note gives semaphore to wake up main loop
 *
 */
void int_callback_rak1904(void)
{
	MYLOG("ACC", "Interrupt triggered");
#ifdef _RAK12500_GNSS_H_
	if ((millis() - last_trigger) > (g_send_repeat_time / 2) && !gnss_active)
#else  // _RAK12500_GNSS_H_
	if ((millis() - last_trigger) > (g_send_repeat_time / 2))
#endif // _RAK12500_GNSS_H_
	{
		motion_detected = true;
		last_trigger = millis();
		// Read the sensors and trigger a packet
		sensor_handler(NULL);
		// Stop a timer
		api.system.timer.stop(RAK_TIMER_0);
		if (g_send_repeat_time != 0)
		{ 
			// Start a timer.
			api.system.timer.start(RAK_TIMER_0, g_send_repeat_time, NULL);
		}
	}
	else
	{
		MYLOG("ACC", "GNSS still active or too less time since last trigger");
		motion_detected = false;
	}
	attachInterrupt(acc_int_pin, int_callback_rak1904, RISING);
	clear_int_rak1904();
}

/**
 * @brief Clear ACC interrupt register to enable next wakeup
 *
 */
void clear_int_rak1904(void)
{
	acc_sensor.readAndClearInterrupt();
	attachInterrupt(acc_int_pin, int_callback_rak1904, RISING);
}

/**
 * @brief Handler for interrupts, called from sensor_handler
 *
 * @return true if GNSS is already active
 * @return false if GNSS is not active
 */
bool handle_rak1904_int(void)
{
	// Reset trigger time
	last_trigger = millis();

	// Just for debug, show if the call is because of a motion detection
	if (motion_detected)
	{
		MYLOG("UPLINK", "ACC triggered IRQ");
		motion_detected = false;
		clear_int_rak1904();
#ifdef _RAK12500_GNSS_H_
		if (gnss_active)
		{
			// digitalWrite(LED_BLUE, LOW);
			// GNSS is already active, do nothing
			return true;
		}
#endif // _RAK12500_GNSS_H_
	}
	return false;
}