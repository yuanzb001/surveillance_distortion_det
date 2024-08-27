class Decode_util():
    slice_type_dic = {0:'P', 1:'B', 2:'I', 3:'SP', 4:'SI', 5:'P', 6:'B', 7:'I', 8:'SP', 9:'SI'}

    @staticmethod
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

    @staticmethod
    def b8(bitstream):
        value = bitstream[:8]
        bitstream = bitstream[8:]
        return value, bitstream
        
    @staticmethod
    def uv(bitstream, num_bits):
        value = 0
        tmp_bitstream = list(bitstream[:num_bits])
        bitstream = bitstream[num_bits:]
        for _ in range(num_bits):
            value = (value << 1) + int(tmp_bitstream.pop(0))
        return value, bitstream
    
    @staticmethod
    def fn(bitstream, num_bits):
    # Generate a fixed-pattern bit string of length n
        value = bitstream[:num_bits]
        bitstream = bitstream[num_bits:]
        return int(value, 2), bitstream
    
    @staticmethod
    def uev(bitstream):
        zeros = 0
        while True:
            tmp_value = bitstream[0]
            bitstream = bitstream[1:]
            if tmp_value == '1':  # Assuming bitstream is a list of '0's and '1's
                break
            zeros += 1
        value = 1 << zeros  # 2^zeros
        for i in range(zeros):
            tmp_value = bitstream[0]
            bitstream = bitstream[1:]
            value += int(tmp_value) << (zeros - 1 - i)
        return value - 1, bitstream

    @staticmethod
    def sev(bitstream):
        # Decode using the previously defined uev function
        ue_value, bitstream = Decode_util.uev(bitstream)  # Assume uev is already defined as shown earlier
        # Map to signed value
        if ue_value % 2 == 0:
            return (-ue_value // 2), bitstream
        else:
            return ((ue_value + 1) // 2), bitstream
    

    @staticmethod
    def aev(bitstream):
        return 0
    
    @staticmethod
    def mev(bitstream):
        return 0