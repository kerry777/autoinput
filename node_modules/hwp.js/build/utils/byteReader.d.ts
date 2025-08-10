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
declare class ByteReader {
    private view;
    private offsetByte;
    constructor(buffer: ArrayBuffer);
    readUInt32(): number;
    readInt32(): number;
    readInt16(): number;
    readUInt16(): number;
    readInt8(): number;
    readUInt8(): number;
    readRecord(): [number, number, number];
    read(byte: number): ArrayBuffer;
    readString(): string;
    remainByte(): number;
    skipByte(offset: number): void;
    isEOF(): boolean;
}
export default ByteReader;
