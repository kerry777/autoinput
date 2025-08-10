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
import { CFB$Container } from 'cfb';
import DocInfo from '../models/docInfo';
import HWPRecord from '../models/record';
declare class DocInfoParser {
    private record;
    private result;
    private container;
    constructor(data: Uint8Array, container: CFB$Container);
    visitDocumentPropertes(record: HWPRecord): void;
    visitCharShape(record: HWPRecord): void;
    visitFaceName(record: HWPRecord): void;
    visitBinData(record: HWPRecord): void;
    visitBorderFill(record: HWPRecord): void;
    visitParagraphShape(record: HWPRecord): void;
    private visit;
    parse(): DocInfo;
}
export default DocInfoParser;
