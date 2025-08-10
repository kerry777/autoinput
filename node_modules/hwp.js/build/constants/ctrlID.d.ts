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
export declare function makeCtrlID(first: string, second: string, third: string, fourth: string): number;
export declare enum CommonCtrlID {
    Table,
    Line,
    Rectangle,
    Ellipse,
    Arc,
    Polygon,
    Curve,
    Equation,
    Picture,
    OLE,
    Connected,
    GenShapeObject
}
export declare enum OtherCtrlID {
    Section,
    Column,
    Header,
    Footer,
    Footnote,
    Endnote,
    AutoNumber,
    NewNumber,
    PageHide,
    PageCT,
    PageNumberPosition,
    Indexmark,
    Bookmark,
    Overlapping,
    Comment,
    HiddenComment
}
export declare enum FieldCtrlID {
    Unknown,
    Date,
    DocDate,
    Path,
    Bookmark,
    MailMerge,
    CrossRef,
    Formula,
    ClickHere,
    Summary,
    UserInfo,
    HyperLink,
    RevisionSign,
    RevisionDelete,
    RevisionAttach,
    RevisionClipping,
    RevisionSawtooth,
    RevisionThinking,
    RevisionPraise,
    RevisionLine,
    RevisionSimpleChange,
    RevisionHyperLink,
    RevisionLineAttach,
    RevisionLineLink,
    RevisionLineRansfer,
    RevisionRightMove,
    RevisionLeftMove,
    RevisionTransfer,
    RevisionSimpleInsert,
    RevisionSplit,
    RevisionChange,
    Memo,
    PrivateInfoSecurity,
    TableOfContents
}
