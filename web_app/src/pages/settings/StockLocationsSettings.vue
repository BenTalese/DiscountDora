<template>
    <q-card flat bordered>
        <q-card-section>
            <div class="text-h6">Stock locations</div>
            <div class="text-caption text-grey">
                Locations now live in a tree (Zone → Area → Section). The new
                Locations page lets you manage them, see attention scores, and
                move items.
            </div>
        </q-card-section>

        <q-separator />

        <q-card-section class="row items-center q-gutter-md">
            <q-icon name="info" size="32px" color="primary" />
            <div class="col">
                Manage zones and their areas/sections from the new
                <strong>Locations</strong> page.
            </div>
            <q-btn
                color="primary"
                no-caps
                icon="open_in_new"
                label="Open Locations"
                to="/locations"
            />
        </q-card-section>
    </q-card>
</template>
