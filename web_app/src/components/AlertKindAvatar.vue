<template>
    <!-- An alert kind's icon in its severity circle. The bell's rows and the
         per-kind toggles on Settings → Notifications both draw it from here
         (owner 2026-10-17: *"keep the alert toggle icons we had before (with
         colour circles) so it's consistent visually with alerts"*), so the
         two cannot drift apart (R-001 / R-003). Decorative: the row beside it
         always names the kind in words (D-014). -->
    <q-avatar :color="colorFor(severity)" text-color="white" size="32px" aria-hidden="true">
        <q-icon :name="iconFor(kind)" size="16px" />
    </q-avatar>
</template>

<script lang="ts" setup>
    import { colorFor, iconFor, type AlertKind, type AlertSeverity } from 'src/models/alert';

    defineProps<{
        kind: AlertKind;
        severity: AlertSeverity;
    }>();
</script>
