import AxiosHttpClient from './axiosHttpClient';

/**
 * One row of `GET /api/data/backup/sections` — the server's backup section
 * catalogue (`restore_shared.SECTIONS`). The Backup & restore page builds
 * its create-dialog, restore tree, sensitive-data warnings and restore
 * report from this; it never carries its own copy (R-003 — the copy it
 * used to carry named `product_barcodes` and lacked nine sections, so the
 * default *New backup* was refused and UI backups omitted recipe steps;
 * finalisation 18-R2 / 18-R3).
 */
export interface BackupSection {
    key: string;
    label: string;
    /** Display grouping — "Core data" / "Optional". */
    category: string;
    /** Ticked by default in the create dialog. */
    default_on: boolean;
    /** Carries data Dora flags before writing it to disk (accounts,
     *  system settings, pricing history). */
    sensitive: boolean;
    /** Offered row-by-row in the restore tree; link/line tables ride
     *  along with their parents and are not pickable. */
    pickable: boolean;
}

/**
 * Admin data endpoints (`/api/data/*`). Started with the section catalogue;
 * the backup library, inspect/restore and spreadsheet-import calls the two
 * data pages still make with raw `fetch` move here under FU-716 (18-R7).
 */
export default class DataApiService {
    private httpClient = new AxiosHttpClient();

    backupSectionsAsync = async (): Promise<BackupSection[]> => {
        const resp = await this.httpClient.get<{ sections: BackupSection[] }>(
            '/data/backup/sections',
        );
        return resp.sections;
    };
}
