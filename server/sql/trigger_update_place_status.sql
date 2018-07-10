CREATE OR REPLACE FUNCTION function_update_place_status()
  RETURNS TRIGGER AS
$BODY$
DECLARE
  _account_id INTEGER;
  _status BOOLEAN;
BEGIN
  SELECT camera.account_id INTO _account_id FROM camera WHERE camera.id = NEW.camera_id;

  SELECT bool_and(place.status) INTO _status FROM place
    INNER JOIN camera
      ON (camera.id = place.camera_id)
  WHERE place.label = NEW.label AND camera.account_id = _account_id;

  UPDATE account
    SET places = jsonb_set(places, format('{%s}', NEW.label)::TEXT[], cast(_status AS TEXT)::jsonb, true)
  WHERE account.id = _account_id;

  RETURN NEW;
END;
$BODY$
LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS trigger_update_place_status ON place CASCADE;


CREATE TRIGGER trigger_update_place_status
  AFTER UPDATE
  ON place
  FOR EACH ROW
  WHEN (NEW.status <> OLD.status)
EXECUTE PROCEDURE function_update_place_status();
