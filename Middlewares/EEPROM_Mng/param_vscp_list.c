/* List of parameters, definition of default values */


#include "param_vscp_list.h"


// Boot flag (jump to application or stay in bootloader)
      U08		vscp_boot_flag;
const U08		vscp_boot_flag_def = 0;

// VSCP nickname id
      U08		vscp_nickname_id;
const U08		vscp_nickname_id_def = 0xFF;

// Segment controller CRC
      U08		vscp_segment_controller_crc;
const U08		vscp_segment_controller_crc_def = 0;

// Node control flags
      U08		vscp_node_control_flags;
const U08		vscp_node_control_flags_def = 0;

// User id 
      VSCP_USER_ID		vscp_user_id;
const VSCP_USER_ID		vscp_user_id_def = {
0,0,0,0,0
};

// GUID
      VSCP_NODE_GUID		vscp_node_guid;
const VSCP_NODE_GUID		vscp_node_guid_def = {
00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00
};

// Node zone
      U08		vscp_node_zone;
const U08		vscp_node_zone_def = 0;

// Node sub zone
      U08		vscp_node_subzone;
const U08		vscp_node_subzone_def = 0;

// Manufacturer device id
      VSCP_MFG_DEVICE_ID		vscp_mfg_device_id;
const VSCP_MFG_DEVICE_ID		vscp_mfg_device_id_def = {
0,0,0,0,0
};

// Manufacturer sub device id
      VSCP_MFG_DEVICE_SUBID		vscp_mfg_device_sub_id;
const VSCP_MFG_DEVICE_SUBID		vscp_mfg_device_sub_id_def = {0};

// MDF URL
      VSCP_MDF_URL		vscp_mdf_url;
const VSCP_MDF_URL		vscp_mdf_url_def = {0};

// Family code
      VSCP_DEVICE_FAMILY_CODE		vscp_device_family_code;
const VSCP_DEVICE_FAMILY_CODE		vscp_device_family_code_def = {0};

// Device type
      VSCP_DEVICE_TYPE		vscp_device_type;
const VSCP_DEVICE_TYPE		vscp_device_type_def = {0};

// Log id (stream)
      U08		vscp_log_id;
const U08		vscp_log_id_def = 0;

// Standard decision matrix
      U08		vscp_std_dm_rows;
const U08		vscp_std_dm_rows_def = 10;

// Decision matrix (standard or extension) row size in bytes
      U08		vscp_std_dm_rows_size;
const U08		vscp_std_dm_rows_size_def = 8;

// Decision matrix next generation
      VSCP_STD_DM		vscp_std_dm;
const VSCP_STD_DM		vscp_std_dm_def = 0;

