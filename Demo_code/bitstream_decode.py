# NAL unit code
import time
from decode_util import Decode_util

def hex_to_bin(hex_string):
        # 初始化二进制字符串
        bin_string = ''
        # 遍历十六进制字符串的每个字符
        for char in hex_string:
            # 将十六进制字符转换为十进制，然后转换为二进制并去掉前缀'0b'
            bin_char = bin(int(char, 16))[2:]
            # 为转换后的二进制字符串补足4位
            bin_char = bin_char.zfill(4)
            # 将处理后的二进制字符串拼接
            bin_string += bin_char
        return bin_string

class NAL_unit:
    def __init__(self, nalu):
        self.nalu = nalu
        self.forbidden_zero_bit = 0
        self.nal_ref_idc = 0
        self.nal_unit_type = -1
        self.rbsp_byte = ''
        self.IdrPicFlag = 0
        

    def nal_unit(self):
        previous_time = time.time()
        # print('len of nalu',len(self.nalu))
        if len(self.nalu) < 50:
            print(self.nalu)
        NumBytesInNALunit = int(len(self.nalu) / 2)
        binary_string = hex_to_bin(self.nalu)
        # print(binary_string[:8])
        # self.forbidden_zero_bit, binary_string = Decode_util.fn(binary_string, 1)
        # self.nal_ref_idc, binary_string = Decode_util.uv(binary_string, 2)
        # print(binary_string[:5])
        binary_string = binary_string[3:]
        self.nal_unit_type, binary_string = Decode_util.uv(binary_string, 5)
        # print(self.nal_unit_type)
        self.IdrPicFlag = 1 if self.nal_unit_type == 5 else 0
        NumBytesInRBSP = 0
        nalUnitHeaderBytes = 1
        # print('nalu unit decode type time: ', previous_time - time.time())

        # if self.nal_unit_type == 14 or self.nal_unit_type == 20 or self.nal_unit_type == 21:
        #     if self.nal_unit_type != 21:
        #         svc_extension_flag, binary_string = Decode_util.uv(binary_string, 1)
        #     else:
        #         avc_3d_extension_flag,binary_string = Decode_util.uv(binary_string, 1)
        #     print("count")
        # Need to be continued
        if self.nal_unit_type in [7, 8]:
            for i in range(nalUnitHeaderBytes, NumBytesInNALunit):
                # print(i)
                if i + 2 < NumBytesInNALunit and binary_string[:24] == hex_to_bin('000003'):
                    b8value, binary_string = Decode_util.b8(binary_string)
                    self.rbsp_byte = self.rbsp_byte + b8value
                    b8value, binary_string = Decode_util.b8(binary_string)
                    self.rbsp_byte = self.rbsp_byte + b8value
                    b8value, binary_string = Decode_util.b8(binary_string)
                    i += 2
                    print('delete emulation_prevention_three_byte')
                else:
                    b8value, binary_string = Decode_util.b8(binary_string)
                    self.rbsp_byte = self.rbsp_byte + b8value

        # print('nalu unit decode: ', previous_time - time.time())


# SPS code
class sps_unit:
    def __init__(self, rbsp_byte):
        self.rbsp_byte = rbsp_byte
        self.seq_parameter_set_id = -1
        self.separate_colour_plane_flag = 0
        self.log2_max_frame_num_minus4 = 0
        self.frame_mbs_only_flag = 0
        self.pic_order_cnt_type = 0
        self.log2_max_pic_order_cnt_lsb_minus4 = 0
        self.delta_pic_order_always_zero_flag = 0
        self.ChromaArrayType = -1
        self.PicSizeInMapUnits = 0
        self.mb_adaptive_frame_field_flag = 0
        self.bit_depth_luma_minus8 = 0
        self.bit_depth_chroma_minus8 = 0
        self.chroma_format_idc = 1
        self.direct_8x8_inference_flag = 1
        self.PicWidthInMbs = 0
        self.FrameHeightInMbs = 0
        self.PicHeightInMapUnits = 0
        
        self.seq_parameter_set_data()
        
    
    def seq_parameter_set_data(self):
        rbsp_byte = self.rbsp_byte
        profile_idc, rbsp_byte = Decode_util.uv(rbsp_byte, 8)
        constraint_set0_flag, rbsp_byte = Decode_util.uv(rbsp_byte, 1)
        constraint_set1_flag, rbsp_byte = Decode_util.uv(rbsp_byte, 1)
        constraint_set2_flag, rbsp_byte = Decode_util.uv(rbsp_byte, 1)
        constraint_set3_flag, rbsp_byte = Decode_util.uv(rbsp_byte, 1)
        constraint_set4_flag, rbsp_byte = Decode_util.uv(rbsp_byte, 1)
        constraint_set5_flag, rbsp_byte = Decode_util.uv(rbsp_byte, 1)
        reserved_zero_2bits, rbsp_byte = Decode_util.uv(rbsp_byte, 2)
        level_idc, rbsp_byte = Decode_util.uv(rbsp_byte, 8)
        self.seq_parameter_set_id, rbsp_byte = Decode_util.uev(rbsp_byte)
        # print('seq_parameter_set_id:', self.seq_parameter_set_id)
        if profile_idc in [100, 110, 122, 244, 44, 83, 86, 118, 128, 138, 139, 134, 135]:
            self.chroma_format_idc, rbsp_byte = Decode_util.uev(rbsp_byte)
            if self.chroma_format_idc == 3:
                self.separate_colour_plane_flag, rbsp_byte = Decode_util.uv(rbsp_byte, 1)
                if self.separate_colour_plane_flag == 0:
                    self.ChromaArrayType = self.chroma_format_idc
                elif self.separate_colour_plane_flag == 1:
                    self.ChromaArrayType = 0
            self.bit_depth_luma_minus8, rbsp_byte = Decode_util.uev(rbsp_byte)
            self.bit_depth_chroma_minus8, rbsp_byte = Decode_util.uev(rbsp_byte)
            qpprime_y_zero_transform_bypass_flag, rbsp_byte = Decode_util.uv(rbsp_byte, 1)
            seq_scaling_matrix_present_flag, rbsp_byte = Decode_util.uv(rbsp_byte, 1)
            if seq_scaling_matrix_present_flag:
                seq_scaling_list_present_flag = []
                for i in range(8 if self.chroma_format_idc != 3 else 12):
                    value, rbsp_byte = Decode_util.uv(rbsp_byte, 1)
                    seq_scaling_list_present_flag.append(value)
                    #need to be contiuned

        self.log2_max_frame_num_minus4, rbsp_byte = Decode_util.uev(rbsp_byte)
        self.pic_order_cnt_type, rbsp_byte = Decode_util.uev(rbsp_byte)
        if self.pic_order_cnt_type == 0:
            self.log2_max_pic_order_cnt_lsb_minus4, rbsp_byte = Decode_util.uev(rbsp_byte)
        elif self.pic_order_cnt_type == 1:
            self.delta_pic_order_always_zero_flag, rbsp_byte = Decode_util.uv(rbsp_byte, 1)
            offset_for_non_ref_pic, rbsp_byte = Decode_util.sev(rbsp_byte)
            offset_for_top_to_bottom_field, rbsp_byte = Decode_util.sev(rbsp_byte)
            num_ref_frames_in_pic_order_cnt_cycle, rbsp_byte = Decode_util.uev(rbsp_byte)
            offset_for_ref_frame = []
            for i in range(num_ref_frames_in_pic_order_cnt_cycle):
                value, rbsp_byte = Decode_util.sev(rbsp_byte)
                offset_for_ref_frame.append(value)
        max_num_ref_frames, rbsp_byte = Decode_util.uev(rbsp_byte)
        # print('max_num_ref_frames:', max_num_ref_frames)
        gaps_in_frame_num_value_allowed_flag, rbsp_byte = Decode_util.uv(rbsp_byte, 1)
        pic_width_in_mbs_minus1, rbsp_byte = Decode_util.uev(rbsp_byte)
        self.PicWidthInMbs = pic_width_in_mbs_minus1 + 1
        pic_height_in_map_units_minus1, rbsp_byte = Decode_util.uev(rbsp_byte)
        self.PicHeightInMapUnits = pic_height_in_map_units_minus1 + 1
        self.PicSizeInMapUnits = self.PicWidthInMbs * self.PicHeightInMapUnits
        self.frame_mbs_only_flag, rbsp_byte = Decode_util.uv(rbsp_byte, 1)
        self.FrameHeightInMbs = ( 2 - self.frame_mbs_only_flag ) * self.PicHeightInMapUnits
        if not self.frame_mbs_only_flag:
            self.mb_adaptive_frame_field_flag, rbsp_byte = Decode_util.uv(rbsp_byte, 1)
        self.direct_8x8_inference_flag, rbsp_byte = Decode_util.uv(rbsp_byte, 1)
        frame_cropping_flag, rbsp_byte = Decode_util.uv(rbsp_byte, 1)
        if frame_cropping_flag:
            frame_crop_left_offset, rbsp_byte = Decode_util.uev(rbsp_byte)
            frame_crop_right_offset, rbsp_byte = Decode_util.uev(rbsp_byte)
            frame_crop_top_offset, rbsp_byte = Decode_util.uev(rbsp_byte)
            frame_crop_bottom_offset, rbsp_byte = Decode_util.uev(rbsp_byte)
        vui_parameters_present_flag, rbsp_byte = Decode_util.uv(rbsp_byte, 1)
        # if vui_parameters_present_flag:
        #     vui_parameters()

# PPS code
class pps_unit:
    def __init__(self, rbsp_byte):
        self.rbsp_byte = rbsp_byte
        self.pic_parameter_set_id = -1
        self.seq_parameter_set_id = -1
        self.bottom_field_pic_order_in_frame_present_flag = 0
        self.redundant_pic_cnt_present_flag = 0
        self.weighted_pred_flag = 0
        self.weighted_bipred_idc = 0
        self.entropy_coding_mode_flag = 0
        self.deblocking_filter_control_present_flag = 0
        self.num_slice_groups_minus1 = 0
        self.slice_group_map_type = 0
        self.SliceGroupChangeRate = 0
        self.transform_8x8_mode_flag = 0
        self.num_ref_idx_l0_default_active_minus1 = 0
        self.num_ref_idx_l1_default_active_minus1 = 0
        self.run_length_minus1 = []
        self.top_left = []
        self.bottom_right = []
        self.slice_group_change_direction_flag = 0
        self.slice_group_change_rate_minus1 = 0
        self.slice_group_id = []
        self.pic_init_qp_minus26 = 0

        self.pic_parameter_set_rbsp()
    
    def pic_parameter_set_rbsp(self):
        rbsp_byte = self.rbsp_byte
        self.pic_parameter_set_id, rbsp_byte = Decode_util.uev(rbsp_byte)
        # print('pic_parameter_set_id:', self.pic_parameter_set_id)
        self.seq_parameter_set_id, rbsp_byte = Decode_util.uev(rbsp_byte)
        # print('seq_parameter_set_id:', self.seq_parameter_set_id)
        # sps_unit = sps_dic[self.seq_parameter_set_id]
        self.entropy_coding_mode_flag, rbsp_byte = Decode_util.uv(rbsp_byte, 1)
        self.bottom_field_pic_order_in_frame_present_flag, rbsp_byte = Decode_util.uv(rbsp_byte, 1)
        self.num_slice_groups_minus1, rbsp_byte = Decode_util.uev(rbsp_byte)
        if self.num_slice_groups_minus1 > 0:
            self.slice_group_map_type, rbsp_byte = Decode_util.uev(rbsp_byte)
            if self.slice_group_map_type == 0:
                for iGroup in range(self.num_slice_groups_minus1):
                    value, rbsp_byte = Decode_util.uev(rbsp_byte)
                    self.run_length_minus1.append(value)
            elif self.slice_group_map_type == 2:
                for iGroup in range(self.num_slice_groups_minus1):
                    value1, rbsp_byte = Decode_util.uev(rbsp_byte)
                    value2, rbsp_byte = Decode_util.uev(rbsp_byte)
                    self.top_left.append(value1)
                    self.bottom_right.append(value2)
            elif self.slice_group_map_type in [3, 4, 5]:
                self.slice_group_change_direction_flag, rbsp_byte = Decode_util.uv(rbsp_byte, 1)
                self.slice_group_change_rate_minus1, rbsp_byte = Decode_util.uev(rbsp_byte)
                self.SliceGroupChangeRate = self.slice_group_change_rate_minus1 + 1
                    
            elif self.slice_group_map_type == 6:
                pic_size_in_map_units_minus1, rbsp_byte = Decode_util.uev(rbsp_byte)
                for i in range(pic_size_in_map_units_minus1):
                    value, rbsp_byte = Decode_util.uv(rbsp_byte, 1)
                    self.slice_group_id.append(value)
        self.num_ref_idx_l0_default_active_minus1, rbsp_byte = Decode_util.uev(rbsp_byte)
        self.num_ref_idx_l1_default_active_minus1, rbsp_byte = Decode_util.uev(rbsp_byte)
        self.weighted_pred_flag, rbsp_byte = Decode_util.uv(rbsp_byte, 1)
        self.weighted_bipred_idc, rbsp_byte = Decode_util.uv(rbsp_byte, 2)
        self.pic_init_qp_minus26, rbsp_byte = Decode_util.sev(rbsp_byte)
        # print('pic_init_qp_minus26:', self.pic_init_qp_minus26)
        chroma_qp_index_offset, rbsp_byte = Decode_util.sev(rbsp_byte)
        self.deblocking_filter_control_present_flag, rbsp_byte = Decode_util.uv(rbsp_byte, 1)
        constrained_intra_pred_flag, rbsp_byte = Decode_util.uv(rbsp_byte, 1)
        self.redundant_pic_cnt_present_flag, rbsp_byte = Decode_util.uv(rbsp_byte, 1)
        # Need to be continued