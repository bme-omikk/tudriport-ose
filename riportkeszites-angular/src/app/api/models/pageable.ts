export class Pageable<T> {
    count: number;
    next: string;
    previous: string;
    page_size: number;
    results: T[];
}