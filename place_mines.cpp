#include "place_mines.h"

#define abs(x) ((x) < 0 ? -(x) : (x))

// 假设导入的msvcrt函数指针已经在另一个地方注册，并可在此文件使用
extern rand_t rand;
extern srand_t srand;
extern malloc_t malloc;
extern free_t free;
extern memset_t memset;
extern memcpy_t memcpy;
extern memcmp_t memcmp;
extern memmove_t memmove;
extern realloc_t realloc;

// 辅助函数：分配二维int数组
int **allocate_assignments(int width, int height) {
    int **assign = (int **)malloc(width * sizeof(int *));
    for (int x = 0; x < width; ++x) {
        assign[x] = (int *)malloc(height * sizeof(int));
        for (int y = 0; y < height; ++y) {
            assign[x][y] = -1; // -1表示未知
        }
    }
    return assign;
}

// 辅助函数：释放二维int数组
void free_assignments(int **assign, int width) {
    for (int x = 0; x < width; ++x) {
        free(assign[x]);
    }
    free(assign);
}

// MineSolver 初始化
void MineSolver_init(MineSolver *solver, Array<Array<int> *> *mines, int width, int height) {
    solver->width = width;
    solver->height = height;
    solver->mines = mines;

    // 初始化 actions
    solver->actions = (Array<Action> *)malloc(sizeof(Array<Action>));
    solver->actions->size = 0;
    solver->actions->capacity = 16;
    solver->actions->growth = 16;
    solver->actions->pad = 0;
    solver->actions->data = (Action *)malloc(solver->actions->capacity * sizeof(Action));

    // 初始化 hints
    solver->hints = (Array<Array<int> *> *)malloc(sizeof(Array<Array<int> *>));
    solver->hints->size = width;
    solver->hints->capacity = width;
    solver->hints->growth = 0;
    solver->hints->pad = 0;
    solver->hints->data = (Array<int> **)malloc(width * sizeof(Array<int> *));
    for (int x = 0; x < width; ++x) {
        solver->hints->data[x] = (Array<int> *)malloc(sizeof(Array<int>));
        solver->hints->data[x]->size = height;
        solver->hints->data[x]->capacity = height;
        solver->hints->data[x]->growth = 0;
        solver->hints->data[x]->pad = 0;
        solver->hints->data[x]->data = (int *)malloc(height * sizeof(int));
        for (int y = 0; y < height; ++y) {
            // 计算每个cell周围的雷数
            int count = 0;
            for (int dx = -1; dx <= 1; ++dx) {
                for (int dy = -1; dy <= 1; ++dy) {
                    if (dx == 0 && dy == 0) continue;
                    int nx = x + dx;
                    int ny = y + dy;
                    if (nx >= 0 && nx < width && ny >= 0 && ny < height) {
                        count += solver->mines->data[nx]->data[ny];
                    }
                }
            }
            solver->hints->data[x]->data[y] = count;
        }
    }

    // 初始化 assignments
    solver->assignments = allocate_assignments(width, height);
}

// 辅助函数：获取邻居
Array<Position> *MineSolver_get_neighbors(MineSolver *solver, int x, int y) {
    Array<Position> *neighbors = (Array<Position> *)malloc(sizeof(Array<Position>));
    neighbors->size = 0;
    neighbors->capacity = 8;
    neighbors->growth = 8;
    neighbors->pad = 0;
    neighbors->data = (Position *)malloc(neighbors->capacity * sizeof(Position));

    for (int dx = -1; dx <= 1; ++dx) {
        for (int dy = -1; dy <= 1; ++dy) {
            if (dx == 0 && dy == 0) continue;
            int nx = x + dx;
            int ny = y + dy;
            if (nx >= 0 && nx < solver->width && ny >= 0 && ny < solver->height) {
                if (neighbors->size >= neighbors->capacity) {
                    neighbors->capacity += neighbors->growth;
                    neighbors->data = (Position *)realloc(neighbors->data, neighbors->capacity * sizeof(Position));
                }
                neighbors->data[neighbors->size].x = nx;
                neighbors->data[neighbors->size].y = ny;
                neighbors->size++;
            }
        }
    }
    return neighbors;
}

// MineSolver 获取未知邻居
Array<Position> *MineSolver_get_unknown_neighbors(MineSolver *solver, int x, int y) {
    Array<Position> *neighbors = MineSolver_get_neighbors(solver, x, y);
    Array<Position> *unknowns = (Array<Position> *)malloc(sizeof(Array<Position>));
    unknowns->size = 0;
    unknowns->capacity = neighbors->size;
    unknowns->growth = neighbors->capacity;
    unknowns->pad = 0;
    unknowns->data = (Position *)malloc(unknowns->capacity * sizeof(Position));

    for (int i = 0; i < neighbors->size; ++i) {
        int nx = neighbors->data[i].x;
        int ny = neighbors->data[i].y;
        if (solver->assignments[nx][ny] == -1) {
            if (unknowns->size >= unknowns->capacity) {
                unknowns->capacity += unknowns->growth;
                unknowns->data = (Position *)realloc(unknowns->data, unknowns->capacity * sizeof(Position));
            }
            unknowns->data[unknowns->size].x = nx;
            unknowns->data[unknowns->size].y = ny;
            unknowns->size++;
        }
    }

    // 释放neighbors
    free(neighbors->data);
    free(neighbors);

    return unknowns;
}

// MineSolver 获取线索
Array<Clue> *MineSolver_get_clues(MineSolver *solver) {
    Array<Clue> *clues = (Array<Clue> *)malloc(sizeof(Array<Clue>));
    clues->size = 0;
    clues->capacity = 16;
    clues->growth = 16;
    clues->pad = 0;
    clues->data = (Clue *)malloc(clues->capacity * sizeof(Clue));

    for (int x = 0; x < solver->width; ++x) {
        for (int y = 0; y < solver->height; ++y) {
            if (solver->assignments[x][y] == 0) { // 安全的
                Array<Position> *unknowns = MineSolver_get_unknown_neighbors(solver, x, y);
                if (unknowns->size == 0) {
                    free(unknowns->data);
                    free(unknowns);
                    continue;
                }
                // 计算剩余的雷数
                int mines_left = solver->hints->data[x]->data[y];
                // 计算已知的雷数
                Array<Position> *neighbors = MineSolver_get_neighbors(solver, x, y);
                for (int i = 0; i < neighbors->size; ++i) {
                    int nx = neighbors->data[i].x;
                    int ny = neighbors->data[i].y;
                    if (solver->assignments[nx][ny] == 1) mines_left--;
                }
                free(neighbors->data);
                free(neighbors);

                // 添加线索
                if (clues->size >= clues->capacity) {
                    clues->capacity += clues->growth;
                    clues->data = (Clue *)realloc(clues->data, clues->capacity * sizeof(Clue));
                }
                clues->data[clues->size].pos.x = x;
                clues->data[clues->size].pos.y = y;
                clues->data[clues->size].unknowns = unknowns;
                clues->data[clues->size].mines = mines_left;
                clues->size++;
            }
        }
    }

    return clues;
}

// MineSolver 传播约束
bool MineSolver_propagate_constraints(MineSolver *solver) {
    bool progress = false;
    Array<Clue> *constraints = MineSolver_get_clues(solver);

    for (int i = 0; i < constraints->size; ++i) {
        Clue *eq = &constraints->data[i];
        Array<Position> *unknowns = eq->unknowns;
        int mines_left = eq->mines;

        if (unknowns->size == 0) continue;

        // 如果剩余雷数等于未知数，全部标记为雷
        if (mines_left == unknowns->size) {
            for (int j = 0; j < unknowns->size; ++j) {
                Position pos = unknowns->data[j];
                if (solver->assignments[pos.x][pos.y] != 1) {
                    solver->assignments[pos.x][pos.y] = 1;
                    // 添加动作
                    if (solver->actions->size >= solver->actions->capacity) {
                        solver->actions->capacity += solver->actions->growth;
                        solver->actions->data = (Action *)realloc(solver->actions->data, solver->actions->capacity * sizeof(Action));
                    }
                    solver->actions->data[solver->actions->size].x = pos.x;
                    solver->actions->data[solver->actions->size].y = pos.y;
                    solver->actions->data[solver->actions->size].is_flag = true;
                    solver->actions->size++;
                    progress = true;
                }
            }
            continue;
        }

        // 如果剩余雷数为0，全部标记为安全
        if (mines_left == 0) {
            for (int j = 0; j < unknowns->size; ++j) {
                Position pos = unknowns->data[j];
                if (solver->assignments[pos.x][pos.y] != 0) {
                    solver->assignments[pos.x][pos.y] = 0;
                    // 添加动作
                    if (solver->actions->size >= solver->actions->capacity) {
                        solver->actions->capacity += solver->actions->growth;
                        solver->actions->data = (Action *)realloc(solver->actions->data, solver->actions->capacity * sizeof(Action));
                    }
                    solver->actions->data[solver->actions->size].x = pos.x;
                    solver->actions->data[solver->actions->size].y = pos.y;
                    solver->actions->data[solver->actions->size].is_flag = false;
                    solver->actions->size++;
                    progress = true;
                }
            }
            continue;
        }

        // 高级推理：子集检查
        for (int k = 0; k < constraints->size; ++k) {
            if (k == i) continue;
            Clue *other_eq = &constraints->data[k];
            bool is_subset = true;
            for (int j = 0; j < other_eq->unknowns->size; ++j) {
                Position pos = other_eq->unknowns->data[j];
                bool found = false;
                for (int m = 0; m < unknowns->size; ++m) {
                    if (unknowns->data[m].x == pos.x && unknowns->data[m].y == pos.y) {
                        found = true;
                        break;
                    }
                }
                if (!found) {
                    is_subset = false;
                    break;
                }
            }
            if (!is_subset) continue;

            // 计算 difference = superset - subset
            Array<Position> *difference = (Array<Position> *)malloc(sizeof(Array<Position>));
            difference->size = 0;
            difference->capacity = unknowns->size;
            difference->growth = unknowns->capacity;
            difference->pad = 0;
            difference->data = (Position *)malloc(difference->capacity * sizeof(Position));

            int mine_difference = eq->mines - other_eq->mines;

            for (int m = 0; m < unknowns->size; ++m) {
                Position pos = unknowns->data[m];
                bool found = false;
                for (int n = 0; n < other_eq->unknowns->size; ++n) {
                    if (other_eq->unknowns->data[n].x == pos.x && other_eq->unknowns->data[n].y == pos.y) {
                        found = true;
                        break;
                    }
                }
                if (!found) {
                    if (difference->size >= difference->capacity) {
                        difference->capacity += difference->growth;
                        difference->data = (Position *)realloc(difference->data, difference->capacity * sizeof(Position));
                    }
                    difference->data[difference->size].x = pos.x;
                    difference->data[difference->size].y = pos.y;
                    difference->size++;
                }
            }

            // 如果 mine_difference 等于 difference 的大小，全部标记为雷
            if (mine_difference == difference->size) {
                for (int j = 0; j < difference->size; ++j) {
                    Position pos = difference->data[j];
                    if (solver->assignments[pos.x][pos.y] != 1) {
                        solver->assignments[pos.x][pos.y] = 1;
                        // 添加动作
                        if (solver->actions->size >= solver->actions->capacity) {
                            solver->actions->capacity += solver->actions->growth;
                            solver->actions->data = (Action *)realloc(solver->actions->data, solver->actions->capacity * sizeof(Action));
                        }
                        solver->actions->data[solver->actions->size].x = pos.x;
                        solver->actions->data[solver->actions->size].y = pos.y;
                        solver->actions->data[solver->actions->size].is_flag = true;
                        solver->actions->size++;
                        progress = true;
                    }
                }
            }
            // 如果 mine_difference 为0，全部标记为安全
            else if (mine_difference == 0) {
                for (int j = 0; j < difference->size; ++j) {
                    Position pos = difference->data[j];
                    if (solver->assignments[pos.x][pos.y] != 0) {
                        solver->assignments[pos.x][pos.y] = 0;
                        // 添加动作
                        if (solver->actions->size >= solver->actions->capacity) {
                            solver->actions->capacity += solver->actions->growth;
                            solver->actions->data = (Action *)realloc(solver->actions->data, solver->actions->capacity * sizeof(Action));
                        }
                        solver->actions->data[solver->actions->size].x = pos.x;
                        solver->actions->data[solver->actions->size].y = pos.y;
                        solver->actions->data[solver->actions->size].is_flag = false;
                        solver->actions->size++;
                        progress = true;
                    }
                }
            }

            // 释放 difference
            free(difference->data);
            free(difference);
        }
    }

    // 释放 constraints
    for (int i = 0; i < constraints->size; ++i) {
        free(constraints->data[i].unknowns->data);
        free(constraints->data[i].unknowns);
    }
    free(constraints->data);
    free(constraints);

    return progress;
}

// MineSolver 解算
Array<Action> *MineSolver_solve(MineSolver *solver, int start_x, int start_y) {
    // 标记起始点为安全
    solver->assignments[start_x][start_y] = 0;
    // 添加动作
    if (solver->actions->size >= solver->actions->capacity) {
        solver->actions->capacity += solver->actions->growth;
        solver->actions->data = (Action *)realloc(solver->actions->data, solver->actions->capacity * sizeof(Action));
    }
    solver->actions->data[solver->actions->size].x = start_x;
    solver->actions->data[solver->actions->size].y = start_y;
    solver->actions->data[solver->actions->size].is_flag = false;
    solver->actions->size++;

    // 迭代传播约束
    while (MineSolver_propagate_constraints(solver)) {
        // 持续传播，直到没有进展
    }

    return solver->actions;
}

// 辅助函数：生成随机数
int get_rand(int max) {
    return rand() % max;
}

// place_mines函数实现
void placeMines(Board *board, int startX, int startY) {
    int width = board->width;
    int height = board->height;
    int mineCount = board->mineCount;

    int oldRandSeed = board->randSeed;
    srand(board->randSeed);
    constexpr int maxAttempts = 500;
    for (int attempts = 0; attempts < maxAttempts; attempts++) {
        // 清空boardMines
        for (int x = 0; x < width; ++x) {
            for (int y = 0; y < height; ++y) {
                board->boardMines->data[x]->data[y] = false;
            }
        }

        // 随机放置雷，避免首次点击及其周围
        int placed = 0;
        while (placed < mineCount) {
            int x = get_rand(width);
            int y = get_rand(height);
            // 检查是否在首次点击及其邻居
            if (abs(x - startX) <= 1 && abs(y - startY) <= 1) continue;
            if (board->boardMines->data[x]->data[y]) continue;
            board->boardMines->data[x]->data[y] = true;
            placed++;
        }

        // 创建 mines 数组
        Array<Array<int> *> *mines = (Array<Array<int> *> *)malloc(sizeof(Array<Array<int> *>));
        mines->size = width;
        mines->capacity = width;
        mines->growth = 0;
        mines->pad = 0;
        mines->data = (Array<int> **)malloc(width * sizeof(Array<int> *));
        for (int x = 0; x < width; ++x) {
            mines->data[x] = (Array<int> *)malloc(sizeof(Array<int>));
            mines->data[x]->size = height;
            mines->data[x]->capacity = height;
            mines->data[x]->growth = 0;
            mines->data[x]->pad = 0;
            mines->data[x]->data = (int *)malloc(height * sizeof(int));
            for (int y = 0; y < height; ++y) {
                mines->data[x]->data[y] = board->boardMines->data[x]->data[y] ? 1 : 0;
            }
        }

        // 初始化 MineSolver
        MineSolver solver;
        MineSolver_init(&solver, mines, width, height);

        // 解算
        Array<Action> *actions = MineSolver_solve(&solver, startX, startY);

        // 检查是否所有 cells 被揭示或标记
        if (actions->size == width * height) {
            // 成功，退出循环
            // 释放资源
            for (int x = 0; x < width; ++x) {
                free(mines->data[x]->data);
                free(mines->data[x]);
            }
            free(mines->data);
            free(mines);

            free_assignments(solver.assignments, width);

            for (int x = 0; x < solver.hints->size; ++x) {
                free(solver.hints->data[x]->data);
                free(solver.hints->data[x]);
            }
            free(solver.hints->data);
            free(solver.hints);

            free(solver.actions->data);
            free(solver.actions);

            break;
        }

        // 释放资源并重试
        for (int x = 0; x < width; ++x) {
            free(mines->data[x]->data);
            free(mines->data[x]);
        }
        free(mines->data);
        free(mines);

        free_assignments(solver.assignments, width);

        for (int x = 0; x < solver.hints->size; ++x) {
            free(solver.hints->data[x]->data);
            free(solver.hints->data[x]);
        }
        free(solver.hints->data);
        free(solver.hints);

        free(solver.actions->data);
        free(solver.actions);
    }

    // 恢复随机种子
    board->randSeed = oldRandSeed;
}
