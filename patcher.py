import os

import pefile
from keystone import *
import subprocess
import lief
import re

def va2foffset(va):
    image_base = pe.OPTIONAL_HEADER.ImageBase
    rva = va - image_base
    for section in pe.sections:
        start = section.VirtualAddress
        end = start + section.SizeOfRawData
        if start <= rva < end:
            file_offset = (rva - section.VirtualAddress) + section.PointerToRawData
            return file_offset
    return None

origin_path = 'Minesweeper.backup.exe'
target_path = 'Minesweeper.exe'
pe = pefile.PE(origin_path)
ks = Ks(KS_ARCH_X86, KS_MODE_64)
place_mines_start = 0x100027614
place_mines_end = 0x1000277E5
place_mines_offset = va2foffset(place_mines_start)  # placeMines 函数的文件

def add_section(section_name, content):
    section_size = len(content)

    print('[+] 计算新节的属性...')
    last_section = pe.sections[-1]

    # 计算新节的对齐地址
    raw_offset = (last_section.PointerToRawData +
                  last_section.SizeOfRawData +
                  pe.OPTIONAL_HEADER.FileAlignment - 1) & ~(pe.OPTIONAL_HEADER.FileAlignment - 1)

    virtual_addr = (last_section.VirtualAddress +
                    last_section.Misc_VirtualSize +
                    pe.OPTIONAL_HEADER.SectionAlignment - 1) & ~(pe.OPTIONAL_HEADER.SectionAlignment - 1)

    print(f'[+] 新节RVA: 0x{virtual_addr:X}')
    print(f'[+] 新节文件偏移: 0x{raw_offset:X}')

    # 创建新节
    new_section = pefile.SectionStructure(pe.__IMAGE_SECTION_HEADER_format__)
    new_section.set_file_offset(pe.sections[-1].get_file_offset() + 40)

    # 设置节的属性
    new_section.Name = section_name.encode().ljust(8, b'\x00')
    new_section.Misc = section_size
    new_section.Misc_PhysicalAddress = 0
    new_section.Misc_VirtualSize = section_size
    new_section.VirtualAddress = virtual_addr
    new_section.SizeOfRawData = section_size
    new_section.PointerToRawData = raw_offset
    new_section.PointerToRelocations = 0
    new_section.PointerToLinenumbers = 0
    new_section.NumberOfRelocations = 0
    new_section.NumberOfLinenumbers = 0
    new_section.Characteristics = 0xE0000020

    # 更新PE头和添加节
    pe.FILE_HEADER.NumberOfSections += 1
    pe.OPTIONAL_HEADER.SizeOfImage = virtual_addr + section_size
    pe.__structures__.append(new_section)
    pe.sections.append(new_section)

    # 写入文件
    print('[+] 写入新文件...')
    pe.write(target_path)

    # 添加数据
    print('[+] 填充指令...')
    with open(target_path, 'r+b') as f:
        f.seek(raw_offset)
        f.write(content)

    print(f'[+] 节添加完成! 大小: 0x{section_size:X} 字节')
    return pe.OPTIONAL_HEADER.ImageBase + virtual_addr


def redirect(new_section_address):
    print('[+] 修改 placeMines 函数...')
    print(f'[+] 跳转到: {new_section_address:#x}')
    try:
        CODE = f'jmp {new_section_address - place_mines_start:#x}'
        encoding, count = ks.asm(CODE, as_bytes=True)

        with open(target_path, 'r+b') as f:
            f.seek(place_mines_offset)
            f.write(encoding)

    except KsError as e:
        print('ERROR: %s' %e)

try:
    os.system('g++ -o place_mines.exe place_mines.h place_mines.cpp -O0 '
              '-nostartfiles -fno-stack-protector -fno-zero-initialized-in-bss -m64 -static -Wl,--no-dynamic-linker')
    os.system('objcopy -O binary place_mines.exe place_mines.bin')

    with open('place_mines.bin', 'rb') as f:
        machine_code = f.read()
        print(f'[+] machine_code 大小: 0x{len(machine_code):X} 字节')

        section_address = add_section('.mines', machine_code)
        place_mines = pefile.PE('place_mines.exe')
        # 获取.start段的偏移
        for section in place_mines.sections:
            if section.Name == b'.start\x00\x00':
                section_start = section.VirtualAddress - place_mines.OPTIONAL_HEADER.AddressOfEntryPoint
                break
        print(f'[+] .start段的偏移: 0x{section_start:X}')
        redirect(section_address + section_start)

except Exception as e:
    print(f'ERROR: {e}')
