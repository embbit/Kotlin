/**
  ******************************************************************************
  * File Name          : main.hpp
  * Description        : This file contains the common defines of the application
  ******************************************************************************
  ** This notice applies to any and all portions of this file
  * that are not between comment pairs USER CODE BEGIN and
  * USER CODE END. Other portions of this file, whether 
  * inserted by the user or by software development tools
  * are owned by their respective copyright owners.
  *
  * COPYRIGHT(c) 2018 STMicroelectronics
  *
  * Redistribution and use in source and binary forms, with or without modification,
  * are permitted provided that the following conditions are met:
  *   1. Redistributions of source code must retain the above copyright notice,
  *      this list of conditions and the following disclaimer.
  *   2. Redistributions in binary form must reproduce the above copyright notice,
  *      this list of conditions and the following disclaimer in the documentation
  *      and/or other materials provided with the distribution.
  *   3. Neither the name of STMicroelectronics nor the names of its contributors
  *      may be used to endorse or promote products derived from this software
  *      without specific prior written permission.
  *
  * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
  * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
  * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
  * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
  * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
  * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
  * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
  * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
  * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
  * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
  *
  ******************************************************************************
  */
/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H
  /* Includes ------------------------------------------------------------------*/

/* Includes ------------------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Private define ------------------------------------------------------------*/
#define VSCP_CORE_PERIOD 100
#define VSCP_TIMER_PERIOD 1000
#define VSCP_LED_PERIOD_FAST 100
#define VSCP_LED_PERIOD_SLOW 800
#define VSCP_CAN_TX_TIMEOUT_MS 10

#define EXT_GPIO_1_Pin GPIO_PIN_13
#define EXT_GPIO_1_GPIO_Port GPIOC
#define EXT_GPIO_2_Pin GPIO_PIN_14
#define EXT_GPIO_2_GPIO_Port GPIOC
#define EXT_GPIO_3_Pin GPIO_PIN_15
#define EXT_GPIO_3_GPIO_Port GPIOC
#define NOTUSED_VSCP_BTN_Pin GPIO_PIN_0
#define NOTUSED_VSCP_BTN_GPIO_Port GPIOC
#define NOTUSED_VSCP_LED_Pin GPIO_PIN_1
#define NOTUSED_VSCP_LED_GPIO_Port GPIOC
#define CH6_REL2_CNTRL_Pin GPIO_PIN_2
#define CH6_REL2_CNTRL_GPIO_Port GPIOC
#define CH6_REL1_CNTRL_Pin GPIO_PIN_3
#define CH6_REL1_CNTRL_GPIO_Port GPIOC
#define CH5_REL2_CNTRL_Pin GPIO_PIN_0
#define CH5_REL2_CNTRL_GPIO_Port GPIOA
#define CH5_REL1_CNTRL_Pin GPIO_PIN_1
#define CH5_REL1_CNTRL_GPIO_Port GPIOA
#define CH4_REL2_CNTRL_Pin GPIO_PIN_2
#define CH4_REL2_CNTRL_GPIO_Port GPIOA
#define CH4_REL1_CNTRL_Pin GPIO_PIN_3
#define CH4_REL1_CNTRL_GPIO_Port GPIOA
#define F_CS_Pin GPIO_PIN_4
#define F_CS_GPIO_Port GPIOA
#define OW_PWR_FAULT_Pin GPIO_PIN_5
#define OW_PWR_FAULT_GPIO_Port GPIOA
#define OW_PWR_EN_Pin GPIO_PIN_6
#define OW_PWR_EN_GPIO_Port GPIOA
#define EXT_GPIO_4_Pin GPIO_PIN_0
#define EXT_GPIO_4_GPIO_Port GPIOB
#define EXT_GPIO_5_Pin GPIO_PIN_1
#define EXT_GPIO_5_GPIO_Port GPIOB
#define EXT_GPIO_6_Pin GPIO_PIN_2
#define EXT_GPIO_6_GPIO_Port GPIOB
#define RS485_RX_Pin GPIO_PIN_10
#define RS485_RX_GPIO_Port GPIOB
#define RS485_RXB11_Pin GPIO_PIN_11
#define RS485_RXB11_GPIO_Port GPIOB
#define RS485_DE_RE_Pin GPIO_PIN_12
#define RS485_DE_RE_GPIO_Port GPIOB
#define EXT_SPI_SCK_Pin GPIO_PIN_13
#define EXT_SPI_SCK_GPIO_Port GPIOB
#define VSCP_BTN_Pin GPIO_PIN_14
#define VSCP_BTN_GPIO_Port GPIOB
#define EXT_SPI_MOSI_Pin GPIO_PIN_15
#define EXT_SPI_MOSI_GPIO_Port GPIOB
#define CH1_REL2_CNTRL_Pin GPIO_PIN_6
#define CH1_REL2_CNTRL_GPIO_Port GPIOC
#define CH1_REL1_CNTRL_Pin GPIO_PIN_7
#define CH1_REL1_CNTRL_GPIO_Port GPIOC
#define CH2_REL2_CNTRL_Pin GPIO_PIN_8
#define CH2_REL2_CNTRL_GPIO_Port GPIOC
#define CH2_REL1_CNTRL_Pin GPIO_PIN_9
#define CH2_REL1_CNTRL_GPIO_Port GPIOC
#define VSCP_LED_Pin GPIO_PIN_8
#define VSCP_LED_GPIO_Port GPIOA
#define CH3_REL1_CNTRL_Pin GPIO_PIN_10
#define CH3_REL1_CNTRL_GPIO_Port GPIOA
#define F_SCK_Pin GPIO_PIN_10
#define F_SCK_GPIO_Port GPIOC
#define F_MISO_Pin GPIO_PIN_11
#define F_MISO_GPIO_Port GPIOC
#define F_MOSI_Pin GPIO_PIN_12
#define F_MOSI_GPIO_Port GPIOC
#define OW_RX_TX_Pin GPIO_PIN_6
#define OW_RX_TX_GPIO_Port GPIOB
#define CAN1_STB_Pin GPIO_PIN_7
#define CAN1_STB_GPIO_Port GPIOB

/* ########################## Assert Selection ############################## */
/**
  * @brief Uncomment the line below to expanse the "assert_param" macro in the 
  *        HAL drivers code
  */
 #define USE_FULL_ASSERT    1U 

/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
 extern "C" {
#endif
void _Error_Handler(char *, int);

#define Error_Handler() _Error_Handler(__FILE__, __LINE__)
#ifdef __cplusplus
}
#endif

/**
  * @}
  */ 

/**
  * @}
*/ 

#endif /* __MAIN_H */
/************************ (C) COPYRIGHT STMicroelectronics *****END OF FILE****/
