/**
 * Copyright Han Lee <hanlee.dev@gmail.com> and other contributors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
import { BaseControl } from './base';
export declare enum ColumnType {
    Normal = 0,
    Parallel = 1,
    Justify = 2
}
export declare enum ColumnDirection {
    Left = 0,
    Right = 1,
    Justify = 2
}
export default class ColumnControl implements BaseControl {
    id: number;
    type: ColumnType;
    count: number;
    direction: ColumnDirection;
    isSameWidth: boolean;
    gap: number;
    widths: number[];
    borderStyle: number;
    borderWidth: number;
    borderColor: number;
}
