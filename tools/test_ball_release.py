import unittest
from extract_issd_ball_release import extract, table, ball_parameter, update_control_charge, ASM, ROOT


class ReleaseTests(unittest.TestCase):
    def test_control_charge_and_limit(self):
        self.assertEqual(update_control_charge(0x80,0x80,10),{'counter':11,'active_mask':0x80})
        self.assertEqual(update_control_charge(0x80,0x80,11),{'counter':11,'active_mask':0})
        self.assertEqual(update_control_charge(0,0x80,5),{'counter':5,'active_mask':0})
        self.assertEqual(update_control_charge(0,0,0),{'counter':0,'active_mask':0})
        with self.assertRaises(ValueError): update_control_charge(-1,0,0)

    def test_parameter_mask_clamp_and_bounds(self):
        data=list(range(64))
        self.assertEqual(ball_parameter(2,0x1f,data),
                         {'type_0430':2,'parameter_0456':11,'table_index':43,'value_0464':43})
        self.assertEqual(ball_parameter(2,0x10,data)['table_index'],32)
        with self.assertRaises(ValueError): ball_parameter(4,0,data)
        with self.assertRaises(ValueError): ball_parameter(-1,0,data)

    def test_word_directive_truncates_bank_like_assembler(self):
        source='DATA_819BB9:\n dw $7ED57A,$843F\n dw $0000\nNEXT:\n'
        self.assertEqual(table(source,'DATA_819BB9',2),[0xD57A,0x843F,0])

    def test_unsupported_expression_is_rejected(self):
        with self.assertRaises(ValueError):
            table('DATA_819BB9:\n dw UNKNOWN+1\nNEXT:\n','DATA_819BB9',2)

    def test_local_rom_tables_and_mutation(self):
        path=ROOT/'International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc'
        if not path.exists() or not ASM.exists(): self.skipTest('Local ROM/disassembly unavailable')
        source=ASM.read_text(encoding='utf-8'); rom=path.read_bytes()
        result=extract(source,rom)
        self.assertEqual(len(result['controller_modes']),9)
        modes=result['controller_modes']
        self.assertEqual([r['automated_route_bit_8000'] for r in modes[0]['records']],[False,True])
        self.assertTrue(all(r['automated_route_bit_8000'] for r in modes[8]['records']))
        self.assertTrue(all(not r['automated_route_bit_8000'] for m in modes[4:8] for r in m['records']))
        self.assertEqual([r['table_value_0464'] for r in result['release_F3CC_by_direction']],
                         [120,120,88,88,120,120,88,88])
        header=len(rom)%0x8000
        changed=bytearray(rom); changed[header+0xDAFE]^=1
        with self.assertRaisesRegex(ValueError,'ROM mismatch'):
            extract(source,bytes(changed))
        # The hash changes with copier header, but decoded records must not.
        self.assertEqual(extract(source,bytes(512)+rom[header:])['controller_modes'],modes)


if __name__=='__main__': unittest.main()
