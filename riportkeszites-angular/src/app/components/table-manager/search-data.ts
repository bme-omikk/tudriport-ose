import { Character } from "src/app/api/models/character";
import { ExtAuthorlist } from "src/app/api/models/ext-author";
import { ExtraField } from "src/app/api/models/extra-field";
import { Type, Typesubtype } from "src/app/api/models/typesubtype";

export class SearchData {
    mode: string = '';
    author: ExtAuthorlist = new ExtAuthorlist();
    year: string = '';
    org: string;
    unit: string;
    subunit: string;
    subsubunit: string;
    yearFrom: number;
    yearTo: number;
    type: Type;
    typesubtype: Typesubtype;
    character: Character;
    pubids: string = "";
    extraFields: ExtraField[] = [];
}