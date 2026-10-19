import unittest

from unlock_d02k import original_usrkey


class NveBackupTest(unittest.TestCase):
    def setUp(self):
        self.key = bytes(range(32))
        raw = bytearray(6_291_456)
        for offset in range(128, 128 + 7 * 128, 128):
            raw[offset - 4:offset] = (315).to_bytes(4, "little")
            raw[offset:offset + 8] = b"USRKEY\0\0"
            raw[offset + 12:offset + 16] = (32).to_bytes(4, "little")
            raw[offset + 20:offset + 52] = self.key
        self.raw = bytes(raw)

    def test_reads_matching_copies(self):
        self.assertEqual(original_usrkey(self.raw), self.key)

    def test_rejects_inconsistent_copy(self):
        raw = bytearray(self.raw)
        last = raw.rfind(b"USRKEY\0\0")
        raw[last + 20] ^= 1
        with self.assertRaises(ValueError):
            original_usrkey(bytes(raw))

    def test_rejects_wrong_partition_size(self):
        with self.assertRaises(ValueError):
            original_usrkey(self.raw[:-1])

    def test_rejects_missing_record(self):
        raw = bytearray(self.raw)
        raw[128:136] = bytes(8)
        with self.assertRaises(ValueError):
            original_usrkey(bytes(raw))

    def test_rejects_wrong_record_number(self):
        raw = bytearray(self.raw)
        raw[124:128] = (314).to_bytes(4, "little")
        with self.assertRaises(ValueError):
            original_usrkey(bytes(raw))

    def test_rejects_wrong_record_size(self):
        raw = bytearray(self.raw)
        raw[140:144] = (31).to_bytes(4, "little")
        with self.assertRaises(ValueError):
            original_usrkey(bytes(raw))


if __name__ == "__main__":
    unittest.main()
