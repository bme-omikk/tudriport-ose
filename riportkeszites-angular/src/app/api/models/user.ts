export class User {
    orgId: string;
    affiliation: string;
    user: {
        username: string;
        email: string;
        first_name: string;
        last_name: string;
        pk: number;
        groups: string[];
        permissions: string[];
    };
}