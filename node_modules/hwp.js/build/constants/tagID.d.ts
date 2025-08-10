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
export declare const HWPTAG_BEGIN: number;
export declare enum DocInfoTagID {
    HWPTAG_DOCUMENT_PROPERTIES,
    HWPTAG_ID_MAPPINGS,
    HWPTAG_BIN_DATA,
    HWPTAG_FACE_NAME,
    HWPTAG_BORDER_FILL,
    HWPTAG_CHAR_SHAPE,
    HWPTAG_TAB_DEF,
    HWPTAG_NUMBERING,
    HWPTAG_BULLET,
    HWPTAG_PARA_SHAPE,
    HWPTAG_STYLE,
    HWPTAG_DOC_DATA,
    HWPTAG_DISTRIBUTE_DOC_DATA,
    RESERVED,
    HWPTAG_COMPATIBLE_DOCUMENT,
    HWPTAG_LAYOUT_COMPATIBILITY,
    HWPTAG_TRACKCHANGE,
    HWPTAG_MEMO_SHAPE,
    HWPTAG_FORBIDDEN_CHAR,
    HWPTAG_TRACK_CHANGE,
    HWPTAG_TRACK_CHANGE_AUTHOR
}
export declare enum SectionTagID {
    HWPTAG_PARA_HEADER,
    HWPTAG_PARA_TEXT,
    HWPTAG_PARA_CHAR_SHAPE,
    HWPTAG_PARA_LINE_SEG,
    HWPTAG_PARA_RANGE_TAG,
    HWPTAG_CTRL_HEADER,
    HWPTAG_LIST_HEADER,
    HWPTAG_PAGE_DEF,
    HWPTAG_FOOTNOTE_SHAPE,
    HWPTAG_PAGE_BORDER_FILL,
    HWPTAG_SHAPE_COMPONENT,
    HWPTAG_TABLE,
    HWPTAG_SHAPE_COMPONENT_LINE,
    HWPTAG_SHAPE_COMPONENT_RECTANGLE,
    HWPTAG_SHAPE_COMPONENT_ELLIPSE,
    HWPTAG_SHAPE_COMPONENT_ARC,
    HWPTAG_SHAPE_COMPONENT_POLYGON,
    HWPTAG_SHAPE_COMPONENT_CURVE,
    HWPTAG_SHAPE_COMPONENT_OLE,
    HWPTAG_SHAPE_COMPONENT_PICTURE,
    HWPTAG_SHAPE_COMPONENT_CONTAINER,
    HWPTAG_CTRL_DATA,
    HWPTAG_EQEDIT,
    RESERVED,
    HWPTAG_SHAPE_COMPONENT_TEXTART,
    HWPTAG_FORM_OBJECT,
    HWPTAG_MEMO_SHAPE,
    HWPTAG_MEMO_LIST,
    HWPTAG_CHART_DATA,
    HWPTAG_VIDEO_DATA,
    HWPTAG_SHAPE_COMPONENT_UNKNOWN
}
