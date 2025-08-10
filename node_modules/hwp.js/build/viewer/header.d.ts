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
declare class Header {
    private pages;
    private observer;
    private container;
    private content;
    private modal;
    private pageNumber;
    private infoButton;
    private printButton;
    constructor(view: HTMLElement, content: HTMLElement, pages: HTMLElement[]);
    updatePageNumber(pageNumber: number): void;
    distory(): void;
    drawContainer(container: HTMLElement): HTMLDivElement;
    drawModal(view: HTMLElement): HTMLDivElement;
    handleModalClick: (event: MouseEvent) => void;
    handleInfoButtionClick: () => void;
    handlePrintButtionClick: () => void;
    drawPageNumber(): void;
    drawInfoIcon(): void;
    drawPrintIcon(): void;
    draw(): void;
}
export default Header;
