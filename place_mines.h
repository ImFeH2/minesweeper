#pragma once
static bool initialized = false;

// 基础类型定义
#define WINAPI __stdcall
using UINT = unsigned int;
using DWORD = unsigned long;
using ULONGLONG = unsigned long long;
using WORD = unsigned short;
using BYTE = unsigned char;
using HMODULE = void *;
using FARPROC = void *;
using LPCSTR = const char *;
using size_t = unsigned long long;

// DOS头
struct IMAGE_DOS_HEADER {
    WORD e_magic; // Magic number
    WORD e_cblp; // Bytes on last page of file
    WORD e_cp; // Pages in file
    WORD e_crlc; // Relocations
    WORD e_cparhdr; // Size of header in paragraphs
    WORD e_minalloc; // Minimum extra paragraphs needed
    WORD e_maxalloc; // Maximum extra paragraphs needed
    WORD e_ss; // Initial (relative) SS value
    WORD e_sp; // Initial SP value
    WORD e_csum; // Checksum
    WORD e_ip; // Initial IP value
    WORD e_cs; // Initial (relative) CS value
    WORD e_lfarlc; // File address of relocation table
    WORD e_ovno; // Overlay number
    WORD e_res[4]; // Reserved words
    WORD e_oemid; // OEM identifier (for e_oeminfo)
    WORD e_oeminfo; // OEM information; e_oemid specific
    WORD e_res2[10]; // Reserved words
    DWORD e_lfanew; // File address of new exe header
};

// 文件头
struct IMAGE_FILE_HEADER {
    WORD Machine;
    WORD NumberOfSections;
    DWORD TimeDateStamp;
    DWORD PointerToSymbolTable;
    DWORD NumberOfSymbols;
    WORD SizeOfOptionalHeader;
    WORD Characteristics;
};

// 数据目录
struct IMAGE_DATA_DIRECTORY {
    DWORD VirtualAddress;
    DWORD Size;
};

// 可选头
struct IMAGE_OPTIONAL_HEADER64 {
    WORD Magic;
    BYTE MajorLinkerVersion;
    BYTE MinorLinkerVersion;
    DWORD SizeOfCode;
    DWORD SizeOfInitializedData;
    DWORD SizeOfUninitializedData;
    DWORD AddressOfEntryPoint;
    DWORD BaseOfCode;
    ULONGLONG ImageBase;
    DWORD SectionAlignment;
    DWORD FileAlignment;
    WORD MajorOperatingSystemVersion;
    WORD MinorOperatingSystemVersion;
    WORD MajorImageVersion;
    WORD MinorImageVersion;
    WORD MajorSubsystemVersion;
    WORD MinorSubsystemVersion;
    DWORD Win32VersionValue;
    DWORD SizeOfImage;
    DWORD SizeOfHeaders;
    DWORD CheckSum;
    WORD Subsystem;
    WORD DllCharacteristics;
    ULONGLONG SizeOfStackReserve;
    ULONGLONG SizeOfStackCommit;
    ULONGLONG SizeOfHeapReserve;
    ULONGLONG SizeOfHeapCommit;
    DWORD LoaderFlags;
    DWORD NumberOfRvaAndSizes;
    IMAGE_DATA_DIRECTORY DataDirectory[16];
};

// NT头
struct IMAGE_NT_HEADERS64 {
    DWORD Signature;
    IMAGE_FILE_HEADER FileHeader;
    IMAGE_OPTIONAL_HEADER64 OptionalHeader;
};

// 导出目录
struct IMAGE_EXPORT_DIRECTORY {
    DWORD Characteristics;
    DWORD TimeDateStamp;
    WORD MajorVersion;
    WORD MinorVersion;
    DWORD Name;
    DWORD Base;
    DWORD NumberOfFunctions;
    DWORD NumberOfNames;
    DWORD AddressOfFunctions; // RVA from base of image
    DWORD AddressOfNames; // RVA from base of image
    DWORD AddressOfNameOrdinals; // RVA from base of image
};

// 区段头
struct IMAGE_SECTION_HEADER {
    BYTE Name[8];

    union {
        DWORD PhysicalAddress;
        DWORD VirtualSize;
    } Misc;

    DWORD VirtualAddress;
    DWORD SizeOfRawData;
    DWORD PointerToRawData;
    DWORD PointerToRelocations;
    DWORD PointerToLinenumbers;
    WORD NumberOfRelocations;
    WORD NumberOfLinenumbers;
    DWORD Characteristics;
};

// 动态数组模板
template<typename T>
class Array {
public:
    int size; // 当前元素数量
    int capacity; // 当前容量
    int growth; // 增长量
    int pad; // 填充
    T *data; // 数据指针
};

// Board类
class Board {
public:
    void *vftable; // 虚函数表指针
    int mineCount; // 雷的数量
    int height; // 高度
    int width; // 宽度
    int flagsPlaced; // 放置的标记数
    int revealedSquares; // 已揭示的方格数
    int revealsAttempted; // 尝试揭示的次数
    int timeElapsed; // 已用时间
    int difficulty; // 难度等级
    int firstXClickPos; // 首次点击的X位置
    int firstYClickPos; // 首次点击的Y位置
    UINT randSeed; // 随机种子
    int padding[7]; // 填充
    Array<Array<int> *> *boardTiles; // 方格数组
    Array<Array<bool> *> *boardMines; // 雷数组
};

// Position结构
struct Position {
    int x;
    int y;
};

// Action结构
struct Action {
    int x;
    int y;
    bool is_flag;
};

// Clue结构
struct Clue {
    Position pos; // 线索方格的位置
    Array<Position> *unknowns; // 未知邻居的列表
    int mines; // 未知邻居中的雷数
};

// MineSolver结构
struct MineSolver {
    int width;
    int height;
    Array<Array<int> *> *mines;
    Array<Action> *actions;
    Array<Array<int> *> *hints;
    int **assignments; // 2D数组, assignments[x][y] = 0 (safe) or 1 (mine) or -1 (unknown)
};

// MineSolver函数声明
void MineSolver_init(MineSolver *solver, Array<Array<int> *> *mines, int width, int height);
Array<Action> *MineSolver_solve(MineSolver *solver, int start_x, int start_y);


__declspec(naked) static ULONGLONG GetKernel32Base() {
    __asm__ __volatile__(
        "movq %gs:0x60, %rax\n\t"
        "movq 0x18(%rax), %rax\n\t"
        "movq 0x30(%rax), %rax\n\t"
        "movq (%rax), %rax\n\t"
        "movq (%rax), %rax\n\t"
        "movq 0x10(%rax), %rax\n\t"
        "ret\n\t"
    );
}

bool strcmp(const char *str1, const char *str2) {
    while (*str1 && *str1 == *str2) {
        str1++;
        str2++;
    }
    return *str1 == *str2;
}

static FARPROC GetFunctionAddress(ULONGLONG moduleBase) {
    auto *pDos = (IMAGE_DOS_HEADER *) moduleBase;
    auto *pNt = (IMAGE_NT_HEADERS64 *) (moduleBase + pDos->e_lfanew);
    auto *pExportDir = &pNt->OptionalHeader.DataDirectory[0]; // IMAGE_DIRECTORY_ENTRY_EXPORT is 0

    auto *pExport = (IMAGE_EXPORT_DIRECTORY *) (moduleBase + pExportDir->VirtualAddress);
    auto *pEAT = (DWORD *) (moduleBase + pExport->AddressOfFunctions);
    auto *pENT = (DWORD *) (moduleBase + pExport->AddressOfNames);
    auto *pEIT = (WORD *) (moduleBase + pExport->AddressOfNameOrdinals);

    for (DWORD i = 0; i < pExport->NumberOfNames; i++) {
        const char *currentName = (const char *) (moduleBase + pENT[i]);
        if (strcmp(currentName, "GetProcAddress")) {
            WORD ordinal = pEIT[i];
            return (FARPROC) (moduleBase + pEAT[ordinal]);
        }
    }
    return nullptr;
}

// Windows API 函数类型定义
using GetProcAddress_t = FARPROC(WINAPI*)(HMODULE hModule, LPCSTR lpProcName);
using LoadLibraryA_t = HMODULE(WINAPI*)(LPCSTR lpLibFileName);
using FreeLibrary_t = int(WINAPI*)(HMODULE hLibModule);

// MSVCRT 函数类型定义
using rand_t = int(*)(void);
using srand_t = void(*)(unsigned int);
using malloc_t = void*(*)(size_t size);
using free_t = void(*)(void* ptr);
using memset_t = void*(*)(void* dest, int val, size_t size);
using memcpy_t = void*(*)(void* dest, const void* src, size_t size);
using memcmp_t = int(*)(const void* ptr1, const void* ptr2, size_t size);
using memmove_t = void*(*)(void* dest, const void* src, size_t size);
using realloc_t = void*(*)(void* ptr, size_t new_size);

// MSVCRT 函数指针
static rand_t rand;
static srand_t srand;
static malloc_t malloc;
static free_t free;
static memset_t memset;
static memcpy_t memcpy;
static memcmp_t memcmp;
static memmove_t memmove;
static realloc_t realloc;

void placeMines(Board *board, int startX, int startY);

__attribute__((section(".start")))
void initialize(Board *board, int startX, int startY) {
    if (initialized) {
        placeMines(board, startX, startY);
        return;
    }

    ULONGLONG kernel32Base = GetKernel32Base();
    if (!kernel32Base) return;

    auto GetProcAddress = (GetProcAddress_t) GetFunctionAddress(kernel32Base);
    if (!GetProcAddress) return;

    auto LoadLibraryA = (LoadLibraryA_t) GetProcAddress((HMODULE) kernel32Base, "LoadLibraryA");
    if (!LoadLibraryA) return;

    HMODULE msvcrt = LoadLibraryA("msvcrt.dll");
    if (!msvcrt) return;

    // 获取基本函数
    rand = (rand_t) GetProcAddress(msvcrt, "rand");
    srand = (srand_t) GetProcAddress(msvcrt, "srand");

    // 获取内存操作函数
    malloc = (malloc_t) GetProcAddress(msvcrt, "malloc");
    free = (free_t) GetProcAddress(msvcrt, "free");
    memset = (memset_t) GetProcAddress(msvcrt, "memset");
    memcpy = (memcpy_t) GetProcAddress(msvcrt, "memcpy");
    memcmp = (memcmp_t) GetProcAddress(msvcrt, "memcmp");
    memmove = (memmove_t) GetProcAddress(msvcrt, "memmove");
    realloc = (realloc_t) GetProcAddress(msvcrt, "realloc");

    if (!rand || !srand || !malloc || !free || !memset ||
        !memcpy || !memcmp || !memmove || !realloc) return;

    initialized = true;
    placeMines(board, startX, startY);
}
