#ifndef _PARAM_VSCP_LIST_H
#define _PARAM_VSCP_LIST_H

#include <utils\tparam.h>	// include library
#include "param_vscp_types.h"	// user type parameters


extern const TPARAM_TBL  param_vscp_table;	// parameters list


// (0) - Boot flag (jump to application or stay in bootloader)
extern       U08		vscp_boot_flag;
extern const U08		vscp_boot_flag_def;
#define      VSCP_BOOT_FLAG_INDX		0

// (1) - VSCP nickname id
extern       U08		vscp_nickname_id;
extern const U08		vscp_nickname_id_def;
#define      VSCP_NICKNAME_ID_INDX		1

// (2) - Segment controller CRC
extern       U08		vscp_segment_controller_crc;
extern const U08		vscp_segment_controller_crc_def;
#define      VSCP_SEGMENT_CONTROLLER_CRC_INDX		2

// (3) - Node control flags
extern       U08		vscp_node_control_flags;
extern const U08		vscp_node_control_flags_def;
#define      VSCP_NODE_CONTROL_FLAGS_INDX		3

// (4) - User id 
extern       VSCP_USER_ID		vscp_user_id;
extern const VSCP_USER_ID		vscp_user_id_def;
#define      VSCP_USER_ID_INDX		4

// (5) - GUID
extern       VSCP_NODE_GUID		vscp_node_guid;
extern const VSCP_NODE_GUID		vscp_node_guid_def;
#define      VSCP_NODE_GUID_INDX		5

// (6) - Node zone
extern       U08		vscp_node_zone;
extern const U08		vscp_node_zone_def;
#define      VSCP_NODE_ZONE_INDX		6

// (7) - Node sub zone
extern       U08		vscp_node_subzone;
extern const U08		vscp_node_subzone_def;
#define      VSCP_NODE_SUBZONE_INDX		7

// (8) - Manufacturer device id
extern       VSCP_MFG_DEVICE_ID		vscp_mfg_device_id;
extern const VSCP_MFG_DEVICE_ID		vscp_mfg_device_id_def;
#define      VSCP_MFG_DEVICE_ID_INDX		8

// (9) - Manufacturer sub device id
extern       VSCP_MFG_DEVICE_SUBID		vscp_mfg_device_sub_id;
extern const VSCP_MFG_DEVICE_SUBID		vscp_mfg_device_sub_id_def;
#define      VSCP_MFG_DEVICE_SUB_ID_INDX		9

// (10) - MDF URL
extern       VSCP_MDF_URL		vscp_mdf_url;
extern const VSCP_MDF_URL		vscp_mdf_url_def;
#define      VSCP_MDF_URL_INDX		10

// (11) - Family code
extern       VSCP_DEVICE_FAMILY_CODE		vscp_device_family_code;
extern const VSCP_DEVICE_FAMILY_CODE		vscp_device_family_code_def;
#define      VSCP_DEVICE_FAMILY_CODE_INDX		11

// (12) - Device type
extern       VSCP_DEVICE_TYPE		vscp_device_type;
extern const VSCP_DEVICE_TYPE		vscp_device_type_def;
#define      VSCP_DEVICE_TYPE_INDX		12

// (13) - Log id (stream)
extern       U08		vscp_log_id;
extern const U08		vscp_log_id_def;
#define      VSCP_LOG_ID_INDX		13

// (14) - Standard decision matrix
extern       U08		vscp_std_dm_rows;
extern const U08		vscp_std_dm_rows_def;
#define      VSCP_STD_DM_ROWS_INDX		14

// (15) - Decision matrix (standard or extension) row size in bytes
extern       U08		vscp_std_dm_rows_size;
extern const U08		vscp_std_dm_rows_size_def;
#define      VSCP_STD_DM_ROWS_SIZE_INDX		15

// (16) - Decision matrix next generation
extern       VSCP_STD_DM		vscp_std_dm;
extern const VSCP_STD_DM		vscp_std_dm_def;
#define      VSCP_STD_DM_INDX		16

#define PARAM_VSCP_IMBUF_SIZE  81 // buffer size for parameters store/restore operation
#if (PARAM_VSCP_IMBUF_SIZE != TPARAM_BUF_SIZE)     /* Check the settings in param_conf.h */

    #error "Parameters size and buffer size are not equal"

#endif

#endif //_PARAM_LIST_VSCP_H

