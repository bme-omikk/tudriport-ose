export class ClientConfig{
    config: RealClientConfig;
    currentLanguage: string;
}
class RealClientConfig{
    mtmt2: MTMT2;
    doi: string;
    gpk_phd_container_urls: GPKContainerUrls;
    user_interface_notifications: UINotifications;
}
class MTMT2{
    publication_list_view_url: string;
    citation_list_view_url: string;
    publication: string;
}
class GPKContainerUrls{
    c: string;
    bc: string;
    j: string;
}
class UINotifications{
    info: string[];
    warning: string[];
    error: string[];
}