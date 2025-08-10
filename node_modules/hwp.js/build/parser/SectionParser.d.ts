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
import { Control } from '../models/controls';
import CommonControl from '../models/controls/common';
import ShapeControl from '../models/controls/shapes/shape';
import TableControl, { TableColumnOption } from '../models/controls/table';
import Section from '../models/section';
import Paragraph from '../models/paragraph';
import HWPRecord from '../models/record';
import ByteReader from '../utils/byteReader';
import RecordReader from '../utils/recordReader';
import { PictureControl } from '../models/controls/shapes';
declare class SectionParser {
    private record;
    private result;
    private content;
    constructor(data: Uint8Array);
    visitPageDef(record: HWPRecord): void;
    visitParaText(record: HWPRecord, paragraph: Paragraph): void;
    visitCharShape(record: HWPRecord, paragraph: Paragraph): void;
    visitCommonControl(reader: ByteReader, control: CommonControl): void;
    visitTableControl(reader: ByteReader): TableControl;
    getControl(reader: ByteReader): Control;
    visitControlHeader(record: HWPRecord, paragraph: Paragraph): void;
    visitCellListHeader(reader: ByteReader): TableColumnOption;
    visitListHeader(record: HWPRecord, reader: RecordReader, control?: Control): void;
    visitTable(record: HWPRecord, control?: TableControl): void;
    visitShapeComponent(record: HWPRecord, paragraph: Paragraph, control: ShapeControl): void;
    visitPicture(record: HWPRecord, control: PictureControl): void;
    visitLineSegment(record: HWPRecord, paragraph: Paragraph): void;
    visit(reader: RecordReader, paragraph: Paragraph, control?: Control): void;
    visitParagraphHeader(record: HWPRecord, content: Paragraph[], control?: Control): void;
    traverse(record: HWPRecord): void;
    parse(): Section;
}
export default SectionParser;
