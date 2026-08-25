/*! @file types.h
* @brief Type definition
*/


#ifndef TYPES_H
#define TYPES_H

#define LITTLE_ENDIAN



/* --------------------------------- */
/* Numerical constants               */
/* --------------------------------- */
/* Boolean values */                         
#define True    (1==1)                      /*!< @brief Definition of True */
#define False   (!True)                     /*!< @brief Definition of False */

#define true    (1==1)                      /*!< @brief Definition of true */
#define false   (!true)                     /*!< @brief Definition of false */

#define OK		True						/*!< @brief Definition of OK condition (e.g. function return value) */
#define NOK		False						/*!< @brief Definition of not OK condition (e.g. function return value) */

#ifndef NULL
#define NULL ((void*)0)                     /*!< @brief NullPointer */
#endif

/* Min/Max-values for the data-types */

#define U8_BIT		8

#define U8_MAX		255
#define U8_MIN		0
#define S8_MAX		127
#define S8_MIN		-128
#define U16_MAX		65535u
#define U16_MIN		0
#define S16_MAX		32767
#define S16_MIN		-32768
#define U32_MAX		4294967295UL
#define U32_MIN		0
#define S32_MAX	 	2147483647L
#define S32_MIN		(-2147483647L-1)



typedef unsigned char      tu8;           /*!< @brief unsigned 8-bit datatype   */
typedef unsigned short int tu16;          /*!< @brief unsigned 16-bit datatype  */
typedef unsigned long int  tu32;          /*!< @brief unsigned 32-bit datatype  */

/* Signed data types */
typedef signed char        ts8;            /*!< @brief signed 8-bit datatype   */
typedef signed short int  ts16;           /*!< @brief signed 16-bit datatype  */
typedef signed long int   ts32;           /*!< @brief signed 32-bit datatype  */
typedef signed char       tBool;          /*!< @brief Boolean Datatype  */



#ifdef BIG_ENDIAN
/*! Word Union bei Big Edian */
typedef union                               /*!< Word data type with single */
{                                           /*!<  accessable bytes */
   struct
   {                                       
      tu8 _H;                             /*!< access HighByte */
      tu8 _L;                             /*!< access LowByte */
   } u8;                                
   tu16 u16;                                 /*!< access u16 */                          
   ts16 s16;                              /*!< access s16 */
} tun16;

/*! dWord Union bei Big Edian */
typedef union                               /*!< u32 data type with single */
{                                           /*!< accessable words and bytes */
   struct
   {                                  
      tu8 _HH;                            /*!< access Byte HH */
      tu8 _HL;                            /*!< access Byte HL */
      tu8 _LH;                            /*!< access Byte LH */
      tu8 _LL;                            /*!< access Byte LL */
   } u8;                                     /*!< Byte access identifier */
   struct
   {                                    
      tu16 _H;                            /*!< access HighWord */
      tu16 _L;                            /*!< access LowWord */
   } u16;                                    /*!< u32 access identifier */
   tu32 u32;                               /*!< s32 access identifier */
   ts32 s32;
} tun32;
#else


#ifdef LITTLE_ENDIAN  
/*! Word Union bei Little Edian */
typedef union                               /*!< Word data type with single */
{                                           /*!<  accessable bytes */
   struct
   {                                       
      tu8 _L;                             /*!< access HighByte */
      tu8 _H;                             /*!< access LowByte */
   } u8;                                
   tu16 u16;                                 /*!< access u16 */                          
   ts16 s16;                              /*!< access s16 */
} tun16;


/*! dWord Union bei Little Edian */
typedef union                               /*!< u32 data type with single */
{                                           /*!< accessable words and bytes */
   struct
   {                                  
      tu8 _LL;                            /*!< access Byte HH */
      tu8 _LH;                            /*!< access Byte HL */
      tu8 _HL;                            /*!< access Byte LH */
      tu8 _HH;                            /*!< access Byte LL */
   } u8;                                     /*!< Byte access identifier */
   struct
   {                                    
      tu16 _L;                            /*!< access HighWord */
      tu16 _H;                            /*!< access LowWord */
   } u16;                                    /*!< u32 access identifier */
   tu32 u32;                               /*!< s32 access identifier */
   ts32 s32;
} tun32;

#else  /*both, Little and Big Endian not defined*/
#error Little/Big Endian not defined!
#endif /* #ifdef LITTLE_ENDIAN */
#endif /* #ifdef BIG_ENDIAN */

typedef void (*tpvFuncPtr) (void);      /*!< Type definition for function      */


#ifndef bit
#define bit(x)	(1 << (x))              /*!< @brief change bit to mask */
#endif

     
#endif

