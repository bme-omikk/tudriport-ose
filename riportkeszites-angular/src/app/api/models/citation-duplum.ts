export class CitationDuplum{
    mtmt_pubid: number;
    label_txt: string;
    citation_duplicate_doi_info: CitationDuplicateDoiInfo[] = [];
    citation_duplicate_title_info: CitationDuplicateTitleInfo[] = [];
    citation_list_not_published: number[] = [];
    citation_list_citingdoc_not_published: number[] = [];
    citation_list_citingdoc_w_error: number[] = [];
    citation_list_unknown_external: number[] = [];
}

class CitationDuplicateDoiInfo{
    doi: string;
    citationList: number[] = [];
    citingDocList: number[] = [];
    citingDocYear: number;
}
class CitationDuplicateTitleInfo{
    title: string;
    citationList: number[] = [];
    citingDocList: number[] = [];
}
