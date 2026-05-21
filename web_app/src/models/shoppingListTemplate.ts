// Mirrors DTOs in dora_api/features/shopping_list_templates/manage_templates.py.

export type TemplateSummary = {
    template_id: string;
    name: string;
    created_at: string;
    updated_at: string;
    line_count: number;
};

export type TemplateLine = {
    line_id: string;
    stock_item_id: string;
    stock_item_name: string;
    quantity: number | null;
    sequence: number;
};

export type TemplateDetail = {
    template_id: string;
    name: string;
    created_at: string;
    updated_at: string;
    lines: TemplateLine[];
};
