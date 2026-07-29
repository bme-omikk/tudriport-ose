export class ExtAuthor {
    org: string = '';
    unit: string = '';
    subunit: string = '';
    subsub_unit: string = '';
    file_data: string = '';
}

export class ExtAuthorlist{
    id: string = '';
    org: string;
    unit: string;
    subunit: string;
    subsub_unit: string;
    mtmtcode: string;
    personname: string = '';
    authorcomment: string = '';
    weighting: string ;
    role: string = '';
    neptuncode: string = '';
    supervisor_mtmt_authid: string;
    for_rollup: Boolean = true;
}